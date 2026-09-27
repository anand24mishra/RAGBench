from qdrant_client import AsyncQdrantClient

from ragbench.app.ingestion.chunker import FixedSizeChunker
from ragbench.app.ingestion.loader import DocumentLoader
from ragbench.app.ingestion.service import IngestionService
from ragbench.app.retrieval.retriever import SemanticRetriever
from ragbench.app.vector_store.qdrant import QdrantVectorStore
from tests.fakes import DeterministicEmbedder


async def test_document_to_qdrant_retrieval_vertical_slice() -> None:
    embedder = DeterministicEmbedder()
    client = AsyncQdrantClient(location=":memory:")
    store = QdrantVectorStore(None, "integration", client=client)
    ingestion = IngestionService(
        DocumentLoader(),
        FixedSizeChunker(chunk_size=1_000, chunk_overlap=0),
        embedder,
        store,
    )

    indexed = await ingestion.ingest("alpha.md", b"# Alpha\nalpha alpha evidence")
    await ingestion.ingest("beta.txt", b"beta beta evidence")
    result = await SemanticRetriever(embedder, store, default_top_k=2).retrieve("alpha", 2)

    assert indexed.status == "indexed"
    assert indexed.chunk_count == 1
    assert len(result.chunks) == 2
    assert result.chunks[0].metadata["filename"] == "alpha.md"
    assert result.chunks[0].document_id == indexed.document_id
    assert result.chunks[0].score > result.chunks[1].score
    await store.close()
