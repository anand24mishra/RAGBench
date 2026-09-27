from __future__ import annotations

import argparse
import asyncio
import json
import logging
import platform
import re
import uuid
from collections import Counter
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from time import perf_counter
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from qdrant_client import AsyncQdrantClient

from benchmarks.timing import (
    ExperimentTimingResult,
    QueryLatency,
    calculate_latency_stats,
)
from evaluation.dataset import (
    compute_corpus_fingerprint,
    compute_dataset_fingerprint,
    load_dataset,
)
from evaluation.evaluator import RetrievalEvaluator, aggregate_metrics
from evaluation.generation_evaluator import (
    DeterministicGenerationEvaluator,
    GenerationEvaluator,
    LLMJudgeGenerationEvaluator,
    extract_content_tokens,
    split_claims,
)
from evaluation.models import (
    EvaluationResult,
    GenerationEvaluationStatus,
    GenerationFailure,
    QueryEvaluationResult,
    ReliabilityMetrics,
    RetrieverConfiguration,
)
from ragbench import __version__ as ragbench_version
from ragbench.app.context.builder import ContextBuilder
from ragbench.app.embeddings.embedder import SentenceTransformerEmbedder
from ragbench.app.generation.base import GenerationResult, LLMProvider
from ragbench.app.generation.provider import OpenAICompatibleProvider
from ragbench.app.ingestion.chunker import FixedSizeChunker
from ragbench.app.ingestion.loader import DocumentLoader
from ragbench.app.ingestion.service import IngestionService
from ragbench.app.pipeline.rag import SYSTEM_PROMPT
from ragbench.app.retrieval.retriever import SemanticRetriever
from ragbench.app.vector_store.qdrant import QdrantVectorStore
from ragbench.cost.models import TokenUsage
from ragbench.cost.pricing import get_pricing_registry

logger = logging.getLogger("ragbench.evaluation.generation")
REPOSITORY_ROOT = Path(__file__).resolve().parent.parent


class GenerationEvaluationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experiment_id: str = Field(default="generation-v4-baseline", min_length=1)
    dataset_version: str = Field(default="1.1.0", min_length=1)
    questions_path: Path = Path("evaluation/dataset/v1.1.0/questions.jsonl")
    dataset_metadata_path: Path = Path("evaluation/dataset/v1.1.0/metadata.json")
    corpus_path: Path = Path("evaluation/dataset/corpus")
    result_path: Path = Path("evaluation/reports/generation_v4_baseline.json")
    summary_path: Path = Path("evaluation/reports/generation_v4_baseline.md")
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_batch_size: int = 32
    chunk_size: int = 800
    chunk_overlap: int = 100
    top_k: int = 5
    generation_model: str = "grounded-deterministic"
    evaluator_type: Literal["deterministic", "llm_judge"] = "deterministic"
    judge_model: str | None = None
    temperature: float = 0.0
    max_output_tokens: int = 500
    qdrant_mode: str = "memory"
    collection_name: str | None = None

    @model_validator(mode="after")
    def validate_config(self) -> GenerationEvaluationConfig:
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        if self.top_k < 1:
            raise ValueError("top_k must be at least 1")
        return self

    def resolve_paths(self, repository_root: Path) -> GenerationEvaluationConfig:
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
        return GenerationEvaluationConfig.model_validate(data)


class GroundedMockLLMProvider(LLMProvider):
    """
    Deterministic provider that constructs answers strictly from retrieved context.

    Extracts relevant context sentences matching question keywords
    without external API dependencies.
    """

    def __init__(self, model_name: str = "grounded-deterministic") -> None:
        self.model_name = model_name

    async def generate(self, prompt: str, *, system_prompt: str) -> GenerationResult:
        # Prompt structure: "Retrieved context:\n\n{context.text}\n\nQuestion:\n{query}"
        context_match = re.search(
            r"Retrieved context:\s*\n\n(.*?)\n\nQuestion:\s*\n(.*)", prompt, re.DOTALL
        )
        if not context_match:
            return GenerationResult(
                text="The available context is insufficient to answer this question.",
                model=self.model_name,
                input_tokens=len(prompt.split()),
                output_tokens=10,
            )

        context_text = context_match.group(1).strip()
        question_text = context_match.group(2).strip()

        if not context_text:
            return GenerationResult(
                text="The available context is insufficient to answer this question.",
                model=self.model_name,
                input_tokens=len(prompt.split()),
                output_tokens=10,
            )

        # Extract content sections from context_text
        content_blocks = re.findall(r"content:\n(.*?)(?=\n\[Source|\Z)", context_text, re.DOTALL)
        if not content_blocks:
            content_blocks = [context_text]

        full_content = "\n".join(b.strip() for b in content_blocks)
        sentences = split_claims(full_content)
        clean_sentences = [
            s.strip()
            for s in sentences
            if not s.startswith("#")
            and not s.startswith("[Source")
            and not s.startswith("filename:")
        ]
        if not clean_sentences:
            clean_sentences = sentences

        question_tokens = set(extract_content_tokens(question_text))

        scored_sentences: list[tuple[float, int, str]] = []
        for idx, sentence in enumerate(clean_sentences):
            sentence_tokens = set(extract_content_tokens(sentence))
            if not sentence_tokens:
                continue
            matched = len(question_tokens & sentence_tokens)
            score = matched / (len(sentence_tokens) ** 0.5)
            scored_sentences.append((score, idx, sentence))

        scored_sentences.sort(key=lambda item: (item[0], -item[1]), reverse=True)

        selected = [s for score, _, s in scored_sentences[:3] if score > 0]
        if not selected and clean_sentences:
            selected = [clean_sentences[0]]

        answer_text = " ".join(selected).strip()
        if not answer_text:
            answer_text = "The available context is insufficient to answer this question."

        return GenerationResult(
            text=answer_text,
            model=self.model_name,
            input_tokens=len(prompt.split()),
            output_tokens=len(answer_text.split()),
        )


def _corpus_files(corpus_path: Path) -> list[Path]:
    supported = DocumentLoader.supported_suffixes
    files = sorted(
        path
        for path in corpus_path.iterdir()
        if path.is_file() and path.suffix.lower() in supported
    )
    if not files:
        raise ValueError(f"No supported corpus documents found in {corpus_path}")
    return files


async def run_generation_evaluation(
    config: GenerationEvaluationConfig,
    *,
    llm_provider: LLMProvider | None = None,
    judge_provider: LLMProvider | None = None,
) -> EvaluationResult:
    dataset = load_dataset(config.questions_path, config.dataset_metadata_path)
    if dataset.version != config.dataset_version:
        raise ValueError(
            f"Configured dataset version {config.dataset_version} does not match {dataset.version}"
        )

    corpus_files = _corpus_files(config.corpus_path)
    corpus_fp = compute_corpus_fingerprint(config.corpus_path)
    dataset_fp = compute_dataset_fingerprint(
        config.questions_path, config.dataset_metadata_path, config.corpus_path
    )

    collection_id = config.collection_name or f"ragbench_eval_gen_{uuid.uuid4().hex[:8]}"

    embedder = SentenceTransformerEmbedder(
        config.embedding_model,
        batch_size=config.embedding_batch_size,
    )
    client = AsyncQdrantClient(location=":memory:")
    store = QdrantVectorStore(None, collection_id, client=client)
    chunker = FixedSizeChunker(config.chunk_size, config.chunk_overlap)
    loader = DocumentLoader()
    ingestion = IngestionService(loader, chunker, embedder, store)
    raw_to_dataset_id: dict[str, str] = {}

    # Initialize LLM Provider for generation
    active_llm: LLMProvider
    if llm_provider is not None:
        active_llm = llm_provider
    elif config.generation_model == "grounded-deterministic":
        active_llm = GroundedMockLLMProvider(model_name=config.generation_model)
    else:
        # Check environment settings
        import os

        api_key = os.environ.get("LLM_API_KEY", "")
        if api_key:
            active_llm = OpenAICompatibleProvider(
                api_key=api_key,
                model=config.generation_model,
                base_url=os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1"),
                timeout_seconds=float(os.environ.get("LLM_TIMEOUT_SECONDS", "30.0")),
                temperature=config.temperature,
                max_tokens=config.max_output_tokens,
            )
        else:
            logger.info("No LLM_API_KEY found; falling back to GroundedMockLLMProvider")
            active_llm = GroundedMockLLMProvider(model_name=config.generation_model)

    # Initialize Generation Evaluator
    evaluator: GenerationEvaluator
    if config.evaluator_type == "llm_judge":
        active_judge = judge_provider or active_llm
        evaluator = LLMJudgeGenerationEvaluator(
            active_judge,
            judge_model=config.judge_model or "judge-model",
            temperature=config.temperature,
        )
    else:
        evaluator = DeterministicGenerationEvaluator()

    context_builder = ContextBuilder(max_characters=4000)

    pricing_registry = get_pricing_registry()
    token_usages: list[TokenUsage] = []
    query_costs = []

    try:
        # Ingest corpus
        for path in corpus_files:
            content = path.read_bytes()
            document = loader.load_bytes(path.name, content, source=str(path))
            raw_to_dataset_id[document.id] = path.stem
            await ingestion.ingest(path.name, content)

        retriever = SemanticRetriever(embedder, store, config.top_k)
        retrieval_evaluator = RetrievalEvaluator(retriever, raw_to_dataset_id)

        eval_start = perf_counter()
        query_results, retrieval_failures = await retrieval_evaluator.evaluate(
            dataset.questions,
            top_k=config.top_k,
        )

        enhanced_queries: list[QueryEvaluationResult] = []
        generation_failures: list[GenerationFailure] = []

        # Execute Generation and Generation Quality Evaluation
        for q_idx, q_eval in enumerate(query_results):
            question_def = dataset.questions[q_idx]

            # Re-fetch or reconstruct retrieval chunks for ContextBuilder
            # q_eval.retrieved has RetrievedDocumentResult
            # We fetch chunk texts from retrieval
            retrieval_res = await retriever.retrieve(question_def.question, config.top_k)
            context = context_builder.build(retrieval_res.chunks)

            # Generate answer
            gen_start = perf_counter()
            if not context.included_chunks:
                generated_answer = "The available context is insufficient to answer this question."
                generation_ms = 0.0
                in_tokens: int | None = 0
                out_tokens: int | None = len(generated_answer.split())
            else:
                prompt = (
                    f"Retrieved context:\n\n{context.text}\n\nQuestion:\n{question_def.question}"
                )
                gen_res = await active_llm.generate(prompt, system_prompt=SYSTEM_PROMPT)
                generation_ms = (perf_counter() - gen_start) * 1000
                generated_answer = gen_res.text
                in_tokens = gen_res.input_tokens
                out_tokens = gen_res.output_tokens

            tot_tokens = (
                (in_tokens + out_tokens)
                if (in_tokens is not None and out_tokens is not None)
                else None
            )
            q_usage = TokenUsage(
                input_tokens=in_tokens,
                output_tokens=out_tokens,
                total_tokens=tot_tokens,
            )
            token_usages.append(q_usage)
            q_cost = pricing_registry.calculate_cost(
                config.generation_model,
                in_tokens,
                out_tokens,
            )
            query_costs.append(q_cost)

            # Evaluate Generation Quality
            eval_res = await evaluator.evaluate(
                question=question_def.question,
                retrieved_context=context.text,
                generated_answer=generated_answer,
                reference_answer=question_def.reference_answer,
                metadata={
                    "required_facts": question_def.required_facts,
                    "relevant_documents": question_def.relevant_documents,
                    "retrieved_documents": q_eval.retrieved_documents,
                },
            )

            total_q_ms = (q_eval.embedding_ms or 0.0) + (q_eval.retrieval_ms or 0.0) + generation_ms

            enhanced_q = QueryEvaluationResult(
                query_id=q_eval.query_id,
                question=q_eval.question,
                relevant_documents=q_eval.relevant_documents,
                retrieved=q_eval.retrieved,
                retrieved_documents=q_eval.retrieved_documents,
                recall_at_1=q_eval.recall_at_1,
                recall_at_3=q_eval.recall_at_3,
                recall_at_5=q_eval.recall_at_5,
                reciprocal_rank=q_eval.reciprocal_rank,
                embedding_ms=q_eval.embedding_ms,
                retrieval_ms=q_eval.retrieval_ms,
                candidate_count=q_eval.candidate_count,
                context=context.text,
                generated_answer=generated_answer,
                reference_answer=question_def.reference_answer,
                generation_metrics=eval_res.metrics,
                generation_ms=generation_ms,
                total_ms=total_q_ms,
                failure_classification=eval_res.failure_classification,
                generation_details=eval_res.details,
                input_tokens=in_tokens,
                output_tokens=out_tokens,
                total_tokens=tot_tokens,
                input_cost=q_cost.input_cost,
                output_cost=q_cost.output_cost,
                total_cost=q_cost.total_cost,
                cost_status=q_cost.cost_status,
            )
            enhanced_queries.append(enhanced_q)

            if eval_res.failure_classification is not None:
                generation_failures.append(
                    GenerationFailure(
                        query_id=question_def.id,
                        failure_type=eval_res.failure_classification,
                        expected_evidence=question_def.relevant_documents,
                        retrieved_evidence=q_eval.retrieved_documents,
                        answer=generated_answer,
                        reference=question_def.reference_answer,
                        failed_metric=eval_res.failure_classification,
                        reason=eval_res.reason or "Evaluation threshold not met",
                    )
                )

        total_runtime_ms = (perf_counter() - eval_start) * 1000

        # Aggregate metrics
        retrieval_metrics = aggregate_metrics(query_results)

        q_count = len(enhanced_queries)
        mean_correctness = (
            sum(q.generation_metrics.correctness for q in enhanced_queries if q.generation_metrics)
            / q_count
        )
        mean_faithfulness = (
            sum(q.generation_metrics.faithfulness for q in enhanced_queries if q.generation_metrics)
            / q_count
        )
        mean_context_relevance = (
            sum(
                q.generation_metrics.context_relevance
                for q in enhanced_queries
                if q.generation_metrics
            )
            / q_count
        )

        combined_metrics = dict(retrieval_metrics)
        combined_metrics.update(
            {
                "correctness": round(mean_correctness, 6),
                "faithfulness": round(mean_faithfulness, 6),
                "context_relevance": round(mean_context_relevance, 6),
            }
        )

        emb_latencies = [q.embedding_ms for q in enhanced_queries if q.embedding_ms is not None]
        ret_latencies = [q.retrieval_ms for q in enhanced_queries if q.retrieval_ms is not None]
        gen_latencies = [q.generation_ms for q in enhanced_queries if q.generation_ms is not None]

        timing: ExperimentTimingResult | None = None
        if emb_latencies and ret_latencies and gen_latencies:
            timing = ExperimentTimingResult(
                sample_size=q_count,
                embedding_latency=calculate_latency_stats(emb_latencies),
                retrieval_latency=calculate_latency_stats(ret_latencies),
                generation_latency=calculate_latency_stats(gen_latencies),
                total_runtime_ms=total_runtime_ms,
                query_latencies=[
                    QueryLatency(
                        query_id=q.query_id,
                        embedding_ms=q.embedding_ms or 0.0,
                        retrieval_ms=q.retrieval_ms or 0.0,
                        generation_ms=q.generation_ms or 0.0,
                        total_ms=q.total_ms or 0.0,
                    )
                    for q in enhanced_queries
                ],
            )

        gen_status = GenerationEvaluationStatus(
            status="evaluated",
            metrics=["correctness", "faithfulness", "context_relevance"],
            evaluator_type=evaluator.evaluator_type,
            generation_model=config.generation_model,
            judge_model=config.judge_model if config.evaluator_type == "llm_judge" else None,
            aggregate_metrics={
                "correctness": round(mean_correctness, 6),
                "faithfulness": round(mean_faithfulness, 6),
                "context_relevance": round(mean_context_relevance, 6),
            },
        )

        cost_accounting = pricing_registry.aggregate_costs(query_costs, token_usages)

        fail_count = sum(1 for q in enhanced_queries if q.failure_classification is not None)
        succ_count = q_count - fail_count
        categories_count = Counter(
            q.failure_classification
            for q in enhanced_queries
            if q.failure_classification is not None
        )
        reliability = ReliabilityMetrics(
            total_requests=q_count,
            successful_requests=succ_count,
            failed_requests=fail_count,
            failure_rate=round(fail_count / q_count, 4) if q_count > 0 else 0.0,
            failure_categories=dict(categories_count),
            timeouts=categories_count.get("timeout", 0),
            provider_errors=categories_count.get("provider_failure", 0),
        )

        return EvaluationResult(
            schema_version="4",
            experiment_id=config.experiment_id,
            timestamp=datetime.now(UTC),
            dataset_name=dataset.name,
            dataset_version=dataset.version,
            dataset_fingerprint=dataset_fp,
            corpus_fingerprint=corpus_fp,
            dataset_question_count=len(dataset.questions),
            dataset_document_count=len(corpus_files),
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
            query_count=q_count,
            metrics=combined_metrics,
            queries=enhanced_queries,
            failures=retrieval_failures,
            generation_evaluation=gen_status,
            generation_model=config.generation_model,
            judge_model=config.judge_model,
            evaluator_type=evaluator.evaluator_type,
            generation_failures=generation_failures,
            timing=timing,
            candidate_count=config.top_k,
            cost_accounting=cost_accounting,
            reliability=reliability,
        )
    finally:
        await store.close()


def write_generation_report(
    result: EvaluationResult, result_path: Path, summary_path: Path
) -> None:
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(
        json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    metrics = result.metrics
    timing = result.timing

    latency_table = ""
    if timing is not None:
        emb = timing.embedding_latency
        ret = timing.retrieval_latency
        gen = timing.generation_latency
        gen_row = (
            f"| Generation | {gen.mean_ms:.3f} | {gen.p50_ms:.3f} | "
            f"{gen.p95_ms:.3f} | {gen.p99_ms:.3f} |\n"
            if gen
            else ""
        )
        latency_table = (
            "\n## Performance & Latency Measurements\n\n"
            f"- **Sample size:** {timing.sample_size} queries\n"
            f"- **Total evaluation runtime:** {timing.total_runtime_ms:.2f} ms\n\n"
            "| Phase | Mean (ms) | p50 (ms) | p95 (ms) | p99 (ms) |\n"
            "| --- | ---: | ---: | ---: | ---: |\n"
            f"| Query Embedding | {emb.mean_ms:.3f} | {emb.p50_ms:.3f} | "
            f"{emb.p95_ms:.3f} | {emb.p99_ms:.3f} |\n"
            f"| Vector Retrieval | {ret.mean_ms:.3f} | {ret.p50_ms:.3f} | "
            f"{ret.p95_ms:.3f} | {ret.p99_ms:.3f} |\n"
            f"{gen_row}"
        )

    # Cost Accounting section
    cost_table = ""
    if result.cost_accounting is not None and result.cost_accounting.cost_status == "available":
        c = result.cost_accounting
        cost_table = (
            "\n## Cost & Token Accounting\n\n"
            f"- **Cost Status:** `{c.cost_status}`\n"
            f"- **Currency:** `{c.currency}`\n"
            f"- **Total Tokens:** {c.total_tokens} "
            f"(Input: {c.input_tokens}, Output: {c.output_tokens})\n"
            f"- **Total Cost:** ${c.total_cost:.6f}\n"
            f"- **Cost per Query:** ${c.cost_per_query:.6f}\n\n"
            "| Item | Value |\n"
            "| --- | ---: |\n"
            f"| Input Tokens | {c.input_tokens or 0} |\n"
            f"| Output Tokens | {c.output_tokens or 0} |\n"
            f"| Total Tokens | {c.total_tokens or 0} |\n"
            f"| Input Cost | ${c.input_cost or 0.0:.6f} |\n"
            f"| Output Cost | ${c.output_cost or 0.0:.6f} |\n"
            f"| Total Cost | ${c.total_cost or 0.0:.6f} |\n"
            f"| Cost per Query | ${c.cost_per_query or 0.0:.6f} |\n"
        )
    elif result.cost_accounting is not None:
        cost_table = (
            "\n## Cost & Token Accounting\n\n"
            "- **Cost Status:** `unavailable` (model pricing not configured)\n"
        )

    # Reliability section
    reliability_table = ""
    if result.reliability is not None:
        rel = result.reliability
        cats = ", ".join(f"{k}: {v}" for k, v in rel.failure_categories.items()) or "None"
        reliability_table = (
            "\n## Reliability & Failure Accounting\n\n"
            f"- **Total Requests:** {rel.total_requests}\n"
            f"- **Successful Requests:** {rel.successful_requests}\n"
            f"- **Failed Requests:** {rel.failed_requests}\n"
            f"- **Failure Rate:** {rel.failure_rate:.2%}\n"
            f"- **Timeouts:** {rel.timeouts}\n"
            f"- **Provider Errors:** {rel.provider_errors}\n"
            f"- **Failure Categories:** {cats}\n"
        )

    # Failure counts
    failure_counts: dict[str, int] = {}
    for f in result.generation_failures:
        failure_counts[f.failure_type] = failure_counts.get(f.failure_type, 0) + 1

    failure_section = "Zero generation failures observed across all evaluation queries."
    if result.generation_failures:
        failure_rows = "\n".join(
            f"| `{f.query_id}` | `{f.failure_type}` | {', '.join(f.expected_evidence)} | "
            f"{f.failed_metric} | {f.reason} |"
            for f in result.generation_failures
        )
        failure_section = (
            f"Observed **{len(result.generation_failures)}** generation failure(s):\n\n"
            "| Query ID | Failure Type | Expected Evidence | Failed Metric | Reason |\n"
            "| --- | --- | --- | --- | --- |\n"
            f"{failure_rows}\n"
        )

    # Per-query debug view (show first 5 queries + all failed queries)
    debug_queries = [q for q in result.queries if q.failure_classification is not None]
    if len(debug_queries) < 5:
        # Include first queries up to 5
        seen = {q.query_id for q in debug_queries}
        for q in result.queries[:5]:
            if q.query_id not in seen:
                debug_queries.append(q)

    debug_cards = []
    for q in debug_queries:
        m = q.generation_metrics
        corr = f"{m.correctness:.2f}" if m else "N/A"
        faith = f"{m.faithfulness:.2f}" if m else "N/A"
        rel = f"{m.context_relevance:.2f}" if m else "N/A"
        fail_badge = f"`{q.failure_classification}`" if q.failure_classification else "PASSED"
        retrieved_list = ", ".join(q.retrieved_documents[:3])
        debug_cards.append(
            f"### Query `{q.query_id}`: *{q.question}*\n\n"
            f"- **Status:** {fail_badge}\n"
            f"- **Expected Document:** {', '.join(q.relevant_documents)}\n"
            f"- **Retrieved Top Documents:** {retrieved_list}\n"
            f'- **Generated Answer:** "{q.generated_answer}"\n'
            f'- **Reference Answer:** "{q.reference_answer or "N/A"}"\n'
            f"- **Metrics:** Correctness: {corr}, Faithfulness: {faith}, Context Relevance: {rel}\n"
        )
    debug_section = "\n".join(debug_cards)

    doc_count = result.dataset_document_count or len(result.corpus_documents)
    q_count = result.dataset_question_count or result.query_count
    c_fingerprint = result.corpus_fingerprint or "N/A"
    judge_name = result.judge_model or "None (deterministic evaluation)"

    summary = (
        f"# Generation Quality Evaluation: `{result.experiment_id}`\n\n"
        f"- **Date:** {result.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        f"- **Dataset:** `{result.dataset_name}` version `{result.dataset_version}`\n"
        f"- **Dataset Fingerprint:** `{result.dataset_fingerprint}`\n"
        f"- **Corpus Fingerprint:** `{c_fingerprint}`\n"
        f"- **Corpus Scope:** {doc_count} documents, {q_count} questions\n"
        f"- **Evaluator Type:** `{result.evaluator_type or 'deterministic'}`\n"
        f"- **Generation Model:** `{result.generation_model or 'N/A'}`\n"
        f"- **Judge Model:** `{judge_name}`\n\n"
        "## Retrieval Quality Metrics\n\n"
        "| Metric | Result |\n"
        "| --- | ---: |\n"
        f"| Recall@1 | {metrics.get('recall_at_1', 0.0):.6f} |\n"
        f"| Recall@3 | {metrics.get('recall_at_3', 0.0):.6f} |\n"
        f"| Recall@5 | {metrics.get('recall_at_5', 0.0):.6f} |\n"
        f"| MRR | {metrics.get('mrr', 0.0):.6f} |\n\n"
        "## Generation Quality Metrics\n\n"
        "| Metric | Result | Description |\n"
        "| --- | ---: | --- |\n"
        f"| Correctness | {metrics.get('correctness', 0.0):.6f} | "
        "Proportion of grounded reference facts satisfied in generated answer |\n"
        f"| Faithfulness | {metrics.get('faithfulness', 0.0):.6f} | "
        "Proportion of generated answer claims directly supported by retrieved context |\n"
        f"| Context Relevance | {metrics.get('context_relevance', 0.0):.6f} | "
        "Proportion of relevant target documents retrieved into context |\n"
        f"{cost_table}"
        f"{reliability_table}"
        f"{latency_table}\n"
        "## Failure Analysis & Classification\n\n"
        f"{failure_section}\n\n"
        "## Per-Query Inspection\n\n"
        f"{debug_section}\n"
    )

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(summary, encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RAGBench V4: Generation Quality Evaluation")
    parser.add_argument(
        "--questions",
        type=Path,
        default=Path("evaluation/dataset/v1.1.0/questions.jsonl"),
        help="Path to questions.jsonl",
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=Path("evaluation/dataset/v1.1.0/metadata.json"),
        help="Path to metadata.json",
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=Path("evaluation/dataset/corpus"),
        help="Path to corpus directory",
    )
    parser.add_argument(
        "--evaluator",
        choices=["deterministic", "llm_judge"],
        default="deterministic",
        help="Evaluator type",
    )
    parser.add_argument(
        "--generation-model",
        type=str,
        default="grounded-deterministic",
        help="Generation model name",
    )
    parser.add_argument(
        "--judge-model",
        type=str,
        default=None,
        help="Judge model name (if evaluator is llm_judge)",
    )
    parser.add_argument(
        "--result-path",
        type=Path,
        default=Path("evaluation/reports/generation_v4_baseline.json"),
        help="Output JSON result path",
    )
    parser.add_argument(
        "--summary-path",
        type=Path,
        default=Path("evaluation/reports/generation_v4_baseline.md"),
        help="Output Markdown summary path",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    config = GenerationEvaluationConfig(
        questions_path=args.questions,
        dataset_metadata_path=args.metadata,
        corpus_path=args.corpus,
        evaluator_type=args.evaluator,
        generation_model=args.generation_model,
        judge_model=args.judge_model,
        result_path=args.result_path,
        summary_path=args.summary_path,
    ).resolve_paths(REPOSITORY_ROOT)

    result = asyncio.run(run_generation_evaluation(config))
    write_generation_report(result, config.result_path, config.summary_path)

    print("RAGBench V4 Generation Quality Evaluation Complete")
    print(f"Queries: {result.query_count}")
    print(f"Correctness:       {result.metrics.get('correctness', 0.0):.6f}")
    print(f"Faithfulness:      {result.metrics.get('faithfulness', 0.0):.6f}")
    print(f"Context Relevance: {result.metrics.get('context_relevance', 0.0):.6f}")
    print(f"Generation Failures: {len(result.generation_failures)}")


if __name__ == "__main__":
    main()
