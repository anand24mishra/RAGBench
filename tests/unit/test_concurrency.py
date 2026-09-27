from __future__ import annotations

import pytest

from benchmarks.concurrency import run_concurrency_benchmark
from ragbench.app.context.builder import ContextBuilder
from ragbench.app.pipeline.rag import RAGPipeline
from ragbench.app.retrieval.retriever import SemanticRetriever
from tests.fakes import DeterministicEmbedder, FakeLLMProvider, MemoryVectorStore


@pytest.mark.asyncio
async def test_concurrency_benchmark_execution() -> None:
    embedder = DeterministicEmbedder()
    store = MemoryVectorStore()
    retriever = SemanticRetriever(embedder, store, default_top_k=3)
    context_builder = ContextBuilder(max_characters=1000)
    llm = FakeLLMProvider(answer="deterministic answer")
    pipeline = RAGPipeline(retriever, context_builder, llm)

    questions = ["What is alpha?", "How does beta work?", "Explain gamma."]
    result = await run_concurrency_benchmark(
        pipeline=pipeline,
        questions=questions,
        concurrency_levels=[1, 2],
        queries_per_level=4,
    )

    assert result.benchmark_id == "concurrency-benchmark"
    assert len(result.levels) == 2
    assert result.levels[0].concurrency == 1
    assert result.levels[0].total_queries == 4
    assert result.levels[0].successful_queries == 4
    assert result.levels[0].failure_rate == 0.0
    assert result.levels[0].latency_stats.mean_ms > 0
    assert result.levels[1].concurrency == 2
    assert result.levels[1].successful_queries == 4

    # Verify serialization
    data = result.model_dump(mode="json")
    assert "levels" in data
    assert len(data["levels"]) == 2
