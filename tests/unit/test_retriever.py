import pytest

from ragbench.app.domain.models import Chunk
from ragbench.app.retrieval.retriever import SemanticRetriever
from tests.fakes import DeterministicEmbedder, MemoryVectorStore


@pytest.mark.asyncio
async def test_retriever_returns_ranked_typed_results_with_scores() -> None:
    embedder = DeterministicEmbedder()
    store = MemoryVectorStore()
    chunks = [
        Chunk(chunk_id="alpha", document_id="a", text="alpha alpha", metadata={}),
        Chunk(chunk_id="beta", document_id="b", text="beta beta", metadata={}),
    ]
    await store.ensure_collection(embedder.dimension)
    await store.upsert(chunks, embedder.embed_documents([chunk.text for chunk in chunks]))

    result = await SemanticRetriever(embedder, store, default_top_k=5).retrieve("alpha", top_k=2)

    assert [item.chunk_id for item in result.chunks] == ["alpha", "beta"]
    assert result.chunks[0].score > result.chunks[1].score
    assert result.embedding_ms >= 0
    assert result.search_ms >= 0
