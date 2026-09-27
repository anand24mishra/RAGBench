from __future__ import annotations

from ragbench.app.domain.errors import EmbeddingError, EmptyDocumentError
from ragbench.app.embeddings.embedder import Embedder
from ragbench.app.ingestion.chunker import FixedSizeChunker
from ragbench.app.ingestion.loader import DocumentLoader
from ragbench.app.schemas.rag import IngestResponse
from ragbench.app.vector_store.base import VectorStore


class IngestionService:
    def __init__(
        self,
        loader: DocumentLoader,
        chunker: FixedSizeChunker,
        embedder: Embedder,
        vector_store: VectorStore,
    ) -> None:
        self.loader = loader
        self.chunker = chunker
        self.embedder = embedder
        self.vector_store = vector_store

    async def ingest(self, filename: str, content: bytes) -> IngestResponse:
        document = self.loader.load_bytes(filename, content)
        chunks = self.chunker.chunk(document)
        if not chunks:
            raise EmptyDocumentError("Document produced no chunks")
        vectors = self.embedder.embed_documents([chunk.text for chunk in chunks])
        if len(vectors) != len(chunks):
            raise EmbeddingError("Embedding output count does not match the chunk count")
        await self.vector_store.ensure_collection(self.embedder.dimension)
        await self.vector_store.upsert(chunks, vectors)
        return IngestResponse(
            document_id=document.id,
            chunk_count=len(chunks),
            status="indexed",
        )
