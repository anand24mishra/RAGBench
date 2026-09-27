from __future__ import annotations

from time import perf_counter

from ragbench.app.domain.models import RetrievalResult
from ragbench.app.embeddings.embedder import Embedder
from ragbench.app.vector_store.base import VectorStore


class SemanticRetriever:
    def __init__(self, embedder: Embedder, vector_store: VectorStore, default_top_k: int) -> None:
        if default_top_k <= 0:
            raise ValueError("default_top_k must be greater than zero")
        self.embedder = embedder
        self.vector_store = vector_store
        self.default_top_k = default_top_k

    async def retrieve(self, query: str, top_k: int | None = None) -> RetrievalResult:
        effective_top_k = top_k or self.default_top_k
        if effective_top_k <= 0:
            raise ValueError("top_k must be greater than zero")

        embedding_started = perf_counter()
        vector = self.embedder.embed_query(query)
        embedding_ms = (perf_counter() - embedding_started) * 1000

        search_started = perf_counter()
        chunks = await self.vector_store.search(vector, effective_top_k)
        search_ms = (perf_counter() - search_started) * 1000
        return RetrievalResult(
            chunks=chunks,
            embedding_ms=embedding_ms,
            search_ms=search_ms,
        )
