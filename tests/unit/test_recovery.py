from __future__ import annotations

import httpx
import pytest

from ragbench.app.context.builder import ContextBuilder
from ragbench.app.domain.errors import (
    EmbeddingError,
    LLMProviderError,
    VectorStoreError,
)
from ragbench.app.domain.models import Chunk
from ragbench.app.generation.base import GenerationResult, LLMProvider
from ragbench.app.generation.provider import OpenAICompatibleProvider
from ragbench.app.pipeline.rag import RAGPipeline
from ragbench.app.retrieval.retriever import SemanticRetriever
from tests.fakes import DeterministicEmbedder, FakeLLMProvider, MemoryVectorStore


class FailingVectorStore(MemoryVectorStore):
    async def search(self, vector, top_k):
        raise VectorStoreError("Vector store connection refused")


class FailingEmbedder(DeterministicEmbedder):
    def embed_query(self, text: str) -> list[float]:
        raise EmbeddingError("Embedding model inference failed")


class MalformedResponseProvider(LLMProvider):
    async def generate(self, prompt: str, *, system_prompt: str) -> GenerationResult:
        raise LLMProviderError("LLM provider returned an invalid response")


@pytest.mark.asyncio
async def test_recovery_vector_store_unavailable() -> None:
    embedder = DeterministicEmbedder()
    store = FailingVectorStore()
    retriever = SemanticRetriever(embedder, store, default_top_k=3)
    pipeline = RAGPipeline(retriever, ContextBuilder(1000), FakeLLMProvider())

    with pytest.raises(VectorStoreError) as exc_info:
        await pipeline.query("test query", top_k=3, request_id="rec-1")
    assert "Vector store connection refused" in str(exc_info.value)
    assert exc_info.value.code == "vector_store_error"


@pytest.mark.asyncio
async def test_recovery_embedding_failure() -> None:
    embedder = FailingEmbedder()
    store = MemoryVectorStore()
    retriever = SemanticRetriever(embedder, store, default_top_k=3)
    pipeline = RAGPipeline(retriever, ContextBuilder(1000), FakeLLMProvider())

    with pytest.raises(EmbeddingError) as exc_info:
        await pipeline.query("test query", top_k=3, request_id="rec-2")
    assert "Embedding model inference failed" in str(exc_info.value)
    assert exc_info.value.code == "embedding_error"


@pytest.mark.asyncio
async def test_recovery_malformed_provider_response() -> None:
    embedder = DeterministicEmbedder()
    store = MemoryVectorStore()
    retriever = SemanticRetriever(embedder, store, default_top_k=3)
    pipeline = RAGPipeline(retriever, ContextBuilder(1000), MalformedResponseProvider())

    c = Chunk(chunk_id="c1", document_id="doc1", text="some context text", metadata={})
    await store.upsert([c], [embedder.embed_query("some context text")])

    with pytest.raises(LLMProviderError) as exc_info:
        await pipeline.query("some query", top_k=3, request_id="rec-3")
    assert exc_info.value.code == "llm_provider_error"


@pytest.mark.asyncio
async def test_recovery_provider_5xx_bounded() -> None:
    call_count = 0

    def mock_503(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(503, text="Service Unavailable", request=request)

    client = httpx.AsyncClient(
        base_url="https://api.openai.com/v1",
        transport=httpx.MockTransport(mock_503),
    )
    provider = OpenAICompatibleProvider(
        api_key="secret-token-12345",
        model="gpt-4o-mini",
        base_url="https://api.openai.com/v1",
        timeout_seconds=0.1,
        temperature=0.0,
        max_tokens=50,
        client=client,
    )

    with pytest.raises(LLMProviderError) as exc_info:
        await provider.generate("test prompt", system_prompt="system")

    # Bounded retries: 3 attempts by default
    assert call_count == 3
    # Verify no secret leaked in exception message
    assert "secret-token" not in str(exc_info.value)


@pytest.mark.asyncio
async def test_recovery_empty_retrieval() -> None:
    embedder = DeterministicEmbedder()
    store = MemoryVectorStore()
    retriever = SemanticRetriever(embedder, store, default_top_k=3)
    pipeline = RAGPipeline(retriever, ContextBuilder(1000), FakeLLMProvider())

    response = await pipeline.query("test question", top_k=3, request_id="rec-4")
    assert response.answer == "The available context is insufficient to answer this question."
    assert len(response.sources) == 0
    assert response.latency.total_ms > 0
