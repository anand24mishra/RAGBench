from __future__ import annotations

from abc import ABC, abstractmethod

from ragbench.app.domain.models import Chunk, RetrievedChunk


class VectorStore(ABC):
    @abstractmethod
    async def ensure_collection(self, dimension: int) -> None: ...

    @abstractmethod
    async def upsert(self, chunks: list[Chunk], vectors: list[list[float]]) -> None: ...

    @abstractmethod
    async def search(self, vector: list[float], top_k: int) -> list[RetrievedChunk]: ...

    @abstractmethod
    async def close(self) -> None: ...
