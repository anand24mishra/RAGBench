from __future__ import annotations

import json
import platform
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from time import perf_counter

from pydantic import BaseModel, ConfigDict, Field
from qdrant_client import AsyncQdrantClient

from benchmarks.timing import LatencyStats, calculate_latency_stats
from evaluation.dataset import load_dataset
from evaluation.runner import EvaluationConfig, _corpus_files
from ragbench import __version__ as ragbench_version
from ragbench.app.embeddings.embedder import SentenceTransformerEmbedder
from ragbench.app.ingestion.chunker import FixedSizeChunker
from ragbench.app.ingestion.loader import DocumentLoader
from ragbench.app.ingestion.service import IngestionService
from ragbench.app.retrieval.retriever import SemanticRetriever
from ragbench.app.vector_store.qdrant import QdrantVectorStore


class BenchmarkEnvironment(BaseModel):
    model_config = ConfigDict(frozen=True)

    python_version: str
    os_name: str
    cpu_architecture: str
    available_accelerator: str
    software_versions: dict[str, str]


def get_benchmark_environment() -> BenchmarkEnvironment:
    accelerator = "cpu"
    try:
        import torch

        if torch.cuda.is_available():
            accelerator = "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            accelerator = "mps"
    except ImportError:
        pass

    software_versions = {
        "ragbench": ragbench_version,
    }
    for pkg in ("qdrant-client", "fastembed", "sentence-transformers"):
        try:
            software_versions[pkg] = version(pkg)
        except Exception:
            pass

    return BenchmarkEnvironment(
        python_version=platform.python_version(),
        os_name=f"{platform.system()} {platform.release()}",
        cpu_architecture=platform.machine(),
        available_accelerator=accelerator,
        software_versions=software_versions,
    )


class BenchmarkConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    warmup_runs: int = Field(default=2, ge=0)
    measurement_runs: int = Field(default=5, ge=1)
    concurrency: int = Field(default=1, ge=1, le=10)


class BenchmarkResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    benchmark_id: str
    timestamp: datetime
    environment: BenchmarkEnvironment
    config: BenchmarkConfig
    embedding_model: str
    embedding_dimension: int
    model_initialization_ms: float
    steady_state_embedding_latency: LatencyStats
    steady_state_retrieval_latency: LatencyStats
    end_to_end_query_latency: LatencyStats
    total_benchmark_runtime_ms: float
    query_count: int
    total_queries_measured: int


async def run_benchmark(
    eval_config: EvaluationConfig,
    bench_config: BenchmarkConfig | None = None,
    output_path: Path | None = None,
) -> BenchmarkResult:
    if bench_config is None:
        bench_config = BenchmarkConfig()

    dataset = load_dataset(eval_config.questions_path, eval_config.dataset_metadata_path)
    benchmark_start = perf_counter()

    init_start = perf_counter()
    embedder = SentenceTransformerEmbedder(
        eval_config.embedding_model,
        batch_size=eval_config.embedding_batch_size,
    )
    model_initialization_ms = (perf_counter() - init_start) * 1000

    client = AsyncQdrantClient(location=":memory:")
    collection_name = f"ragbench_bench_{eval_config.experiment_id}_{int(benchmark_start)}"
    store = QdrantVectorStore(None, collection_name, client=client)
    chunker = FixedSizeChunker(eval_config.chunk_size, eval_config.chunk_overlap)
    loader = DocumentLoader()
    ingestion = IngestionService(loader, chunker, embedder, store)

    try:
        corpus_files = _corpus_files(eval_config.corpus_path)
        for path in corpus_files:
            await ingestion.ingest(path.name, path.read_bytes())

        retriever = SemanticRetriever(embedder, store, eval_config.top_k)

        # Warm-up phase
        for _ in range(bench_config.warmup_runs):
            for question in dataset.questions:
                await retriever.retrieve(question.question, eval_config.top_k)

        # Measurement phase
        embedding_latencies: list[float] = []
        retrieval_latencies: list[float] = []
        end_to_end_latencies: list[float] = []

        for _ in range(bench_config.measurement_runs):
            for question in dataset.questions:
                q_start = perf_counter()
                retrieval = await retriever.retrieve(question.question, eval_config.top_k)
                q_total_ms = (perf_counter() - q_start) * 1000

                embedding_latencies.append(retrieval.embedding_ms)
                retrieval_latencies.append(retrieval.search_ms)
                end_to_end_latencies.append(q_total_ms)

        total_runtime_ms = (perf_counter() - benchmark_start) * 1000

        return BenchmarkResult(
            benchmark_id=f"bench-{eval_config.experiment_id}",
            timestamp=datetime.now(UTC),
            environment=get_benchmark_environment(),
            config=bench_config,
            embedding_model=eval_config.embedding_model,
            embedding_dimension=embedder.dimension,
            model_initialization_ms=model_initialization_ms,
            steady_state_embedding_latency=calculate_latency_stats(embedding_latencies),
            steady_state_retrieval_latency=calculate_latency_stats(retrieval_latencies),
            end_to_end_query_latency=calculate_latency_stats(end_to_end_latencies),
            total_benchmark_runtime_ms=total_runtime_ms,
            query_count=len(dataset.questions),
            total_queries_measured=len(embedding_latencies),
        )
    finally:
        await store.close()


def write_benchmark_result(result: BenchmarkResult, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
