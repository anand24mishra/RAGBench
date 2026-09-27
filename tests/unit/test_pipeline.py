import pytest

from ragbench.app.context.builder import ContextBuilder
from ragbench.app.domain.models import Chunk
from ragbench.app.pipeline.rag import RAGPipeline
from ragbench.app.retrieval.retriever import SemanticRetriever
from tests.fakes import DeterministicEmbedder, FakeLLMProvider, MemoryVectorStore


@pytest.mark.asyncio
async def test_pipeline_returns_sources_usage_and_timings() -> None:
    embedder = DeterministicEmbedder()
    store = MemoryVectorStore()
    chunk = Chunk(
        chunk_id="alpha",
        document_id="doc-alpha",
        text="alpha evidence",
        metadata={"filename": "alpha.txt"},
    )
    await store.ensure_collection(embedder.dimension)
    await store.upsert([chunk], embedder.embed_documents([chunk.text]))
    llm = FakeLLMProvider()
    pipeline = RAGPipeline(
        SemanticRetriever(embedder, store, 5),
        ContextBuilder(1_000),
        llm,
    )

    response = await pipeline.query("alpha", 1, request_id="request-1")

    assert response.answer == "Answer based on context."
    assert response.sources[0].chunk_id == "alpha"
    assert response.usage.model == "fake-model"
    assert response.usage.input_tokens == 12
    assert response.latency.total_ms >= response.latency.generation_ms
    assert len(llm.calls) == 1
    assert "alpha evidence" in llm.calls[0][0]


@pytest.mark.asyncio
async def test_pipeline_does_not_call_llm_without_retrieval_results() -> None:
    llm = FakeLLMProvider()
    pipeline = RAGPipeline(
        SemanticRetriever(DeterministicEmbedder(), MemoryVectorStore(), 5),
        ContextBuilder(1_000),
        llm,
    )

    response = await pipeline.query("missing", 1, request_id="request-2")

    assert "insufficient" in response.answer.lower()
    assert response.sources == []
    assert response.latency.generation_ms == 0
    assert llm.calls == []
