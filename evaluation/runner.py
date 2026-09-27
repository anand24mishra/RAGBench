from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import platform
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from time import perf_counter

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator
from qdrant_client import AsyncQdrantClient

from benchmarks.timing import ExperimentTimingResult, QueryLatency, calculate_latency_stats
from evaluation.comparison import compare_results, load_evaluation_result, write_comparison
from evaluation.dataset import load_dataset
from evaluation.evaluator import RetrievalEvaluator, aggregate_metrics
from evaluation.models import EvaluationResult, RetrieverConfiguration
from ragbench import __version__ as ragbench_version
from ragbench.app.embeddings.embedder import SentenceTransformerEmbedder
from ragbench.app.ingestion.chunker import FixedSizeChunker
from ragbench.app.ingestion.loader import DocumentLoader
from ragbench.app.ingestion.service import IngestionService
from ragbench.app.retrieval.retriever import SemanticRetriever
from ragbench.app.vector_store.qdrant import QdrantVectorStore

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPOSITORY_ROOT / "experiments" / "baseline" / "config.yaml"


class EvaluationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experiment_id: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    questions_path: Path
    dataset_metadata_path: Path
    corpus_path: Path
    result_path: Path
    summary_path: Path
    embedding_model: str = Field(min_length=1)
    embedding_batch_size: int = Field(gt=0)
    chunk_size: int = Field(gt=0)
    chunk_overlap: int = Field(ge=0)
    top_k: int = Field(ge=1, le=100)
    qdrant_mode: str = "memory"
    collection_name: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_configuration(self) -> EvaluationConfig:
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        if self.qdrant_mode != "memory":
            raise ValueError("V2 evaluation supports qdrant_mode=memory only")
        return self

    def resolve_paths(self, repository_root: Path) -> EvaluationConfig:
        data = self.model_dump()
        for field_name in (
            "questions_path",
            "dataset_metadata_path",
            "corpus_path",
            "result_path",
            "summary_path",
        ):
            path = data[field_name]
            if not path.is_absolute():
                data[field_name] = repository_root / path
        return EvaluationConfig.model_validate(data)


def load_config(path: Path) -> EvaluationConfig:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        return EvaluationConfig.model_validate(raw).resolve_paths(REPOSITORY_ROOT)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        raise ValueError(f"Invalid evaluation configuration: {path}") from exc


def _corpus_files(corpus_path: Path) -> list[Path]:
    supported = DocumentLoader.supported_suffixes
    files = sorted(
        path
        for path in corpus_path.iterdir()
        if path.is_file() and path.suffix.lower() in supported
    )
    if not files:
        raise ValueError(f"No supported corpus documents found in {corpus_path}")
    if len({path.stem for path in files}) != len(files):
        raise ValueError("Corpus filenames must have unique stems")
    return files


def _dataset_fingerprint(config: EvaluationConfig, corpus_files: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in [config.dataset_metadata_path, config.questions_path, *corpus_files]:
        digest.update(path.name.encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


async def run_evaluation(config: EvaluationConfig) -> EvaluationResult:
    dataset = load_dataset(config.questions_path, config.dataset_metadata_path)
    if dataset.version != config.dataset_version:
        raise ValueError(
            f"Configured dataset version {config.dataset_version} does not match {dataset.version}"
        )

    embedder = SentenceTransformerEmbedder(
        config.embedding_model,
        batch_size=config.embedding_batch_size,
    )
    client = AsyncQdrantClient(location=":memory:")
    store = QdrantVectorStore(None, config.collection_name, client=client)
    chunker = FixedSizeChunker(config.chunk_size, config.chunk_overlap)
    loader = DocumentLoader()
    ingestion = IngestionService(loader, chunker, embedder, store)
    raw_to_dataset_id: dict[str, str] = {}

    try:
        corpus_files = _corpus_files(config.corpus_path)
        corpus_ids = {path.stem for path in corpus_files}
        metadata = json.loads(config.dataset_metadata_path.read_text(encoding="utf-8"))
        if corpus_ids != set(metadata["document_ids"]):
            raise ValueError("Corpus document IDs do not match dataset metadata")

        for path in corpus_files:
            content = path.read_bytes()
            document = loader.load_bytes(path.name, content, source=str(path))
            raw_to_dataset_id[document.id] = path.stem
            await ingestion.ingest(path.name, content)

        eval_start = perf_counter()
        retriever = SemanticRetriever(embedder, store, config.top_k)
        evaluator = RetrievalEvaluator(retriever, raw_to_dataset_id)
        query_results, failures = await evaluator.evaluate(
            dataset.questions,
            top_k=config.top_k,
        )
        total_eval_time_ms = (perf_counter() - eval_start) * 1000
        metrics = aggregate_metrics(query_results)

        emb_latencies = [q.embedding_ms for q in query_results if q.embedding_ms is not None]
        ret_latencies = [q.retrieval_ms for q in query_results if q.retrieval_ms is not None]

        timing = None
        if emb_latencies and ret_latencies:
            timing = ExperimentTimingResult(
                sample_size=len(query_results),
                embedding_latency=calculate_latency_stats(emb_latencies),
                retrieval_latency=calculate_latency_stats(ret_latencies),
                total_runtime_ms=total_eval_time_ms,
                query_latencies=[
                    QueryLatency(
                        query_id=q.query_id,
                        embedding_ms=q.embedding_ms or 0.0,
                        retrieval_ms=q.retrieval_ms or 0.0,
                        total_ms=(q.embedding_ms or 0.0) + (q.retrieval_ms or 0.0),
                    )
                    for q in query_results
                ],
            )

        return EvaluationResult(
            experiment_id=config.experiment_id,
            timestamp=datetime.now(UTC),
            dataset_name=dataset.name,
            dataset_version=dataset.version,
            dataset_fingerprint=_dataset_fingerprint(config, corpus_files),
            corpus_documents={
                dataset_id: raw_id for raw_id, dataset_id in sorted(raw_to_dataset_id.items())
            },
            retriever_configuration=RetrieverConfiguration(
                chunk_size=config.chunk_size,
                chunk_overlap=config.chunk_overlap,
                embedding_batch_size=config.embedding_batch_size,
                qdrant_mode="memory",
            ),
            embedding_model=config.embedding_model,
            embedding_dimension=embedder.dimension,
            software_versions={
                "ragbench": ragbench_version,
                "python": platform.python_version(),
                "qdrant-client": version("qdrant-client"),
                "sentence-transformers": version("sentence-transformers"),
            },
            top_k=config.top_k,
            query_count=len(query_results),
            metrics=metrics,
            queries=query_results,
            failures=failures,
            timing=timing,
            candidate_count=config.top_k,
        )
    finally:
        await store.close()


def write_result(result: EvaluationResult, result_path: Path, summary_path: Path) -> None:
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(
        json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    metrics = result.metrics
    timing_section = ""
    if result.timing is not None:
        emb = result.timing.embedding_latency
        ret = result.timing.retrieval_latency
        timing_section = (
            "\n### Latency measurements\n\n"
            f"- Sample size: {result.timing.sample_size} queries\n"
            f"- Total evaluation runtime: {result.timing.total_runtime_ms:.2f} ms\n\n"
            "| Phase | Mean (ms) | p50 (ms) | p95 (ms) | p99 (ms) |\n"
            "| --- | ---: | ---: | ---: | ---: |\n"
            f"| Query embedding | {emb.mean_ms:.3f} | {emb.p50_ms:.3f} | "
            f"{emb.p95_ms:.3f} | {emb.p99_ms:.3f} |\n"
            f"| Vector retrieval | {ret.mean_ms:.3f} | {ret.p50_ms:.3f} | "
            f"{ret.p95_ms:.3f} | {ret.p99_ms:.3f} |\n"
        )

    summary = (
        "# RAGBench Evaluation\n\n"
        f"- Experiment: `{result.experiment_id}`\n"
        f"- Dataset: `{result.dataset_name}` version `{result.dataset_version}`\n"
        f"- Queries: {result.query_count}\n"
        f"- Top-k retrieval depth: {result.top_k}\n"
        f"- Retrieval failures at top-k: {len(result.failures)}\n\n"
        "| Metric | Result |\n"
        "| --- | ---: |\n"
        f"| Recall@1 | {metrics['recall_at_1']:.6f} |\n"
        f"| Recall@3 | {metrics['recall_at_3']:.6f} |\n"
        f"| Recall@5 | {metrics['recall_at_5']:.6f} |\n"
        f"| MRR | {metrics['mrr']:.6f} |\n"
        f"{timing_section}\n"
        "Generation evaluation: Not implemented.\n"
    )
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(summary, encoding="utf-8")


def print_summary(result: EvaluationResult) -> None:
    print("RAGBench Evaluation")
    print(f"Queries: {result.query_count}")
    print()
    print(f"Recall@1: {result.metrics['recall_at_1']:.6f}")
    print(f"Recall@3: {result.metrics['recall_at_3']:.6f}")
    print(f"Recall@5: {result.metrics['recall_at_5']:.6f}")
    print(f"MRR:      {result.metrics['mrr']:.6f}")
    print(f"Failures: {len(result.failures)}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run or compare RAGBench evaluations")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--compare", nargs=2, type=Path, metavar=("BASELINE", "EXPERIMENT"))
    parser.add_argument("--output", type=Path)
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    if args.compare:
        baseline = load_evaluation_result(args.compare[0])
        experiment = load_evaluation_result(args.compare[1])
        comparison = compare_results(baseline, experiment)
        if args.output:
            write_comparison(comparison, args.output)
        print(json.dumps(comparison.model_dump(mode="json"), indent=2, sort_keys=True))
        return

    config = load_config(args.config)
    result = asyncio.run(run_evaluation(config))
    write_result(result, config.result_path, config.summary_path)
    print_summary(result)


if __name__ == "__main__":
    main()
