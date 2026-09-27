from __future__ import annotations

import math

from ragbench.app.domain.models import Chunk, RetrievedChunk
from ragbench.app.embeddings.embedder import Embedder
from ragbench.app.generation.base import GenerationResult, LLMProvider
from ragbench.app.vector_store.base import VectorStore


class DeterministicEmbedder(Embedder):
    @property
    def dimension(self) -> int:
        return 4

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    @staticmethod
    def _embed(text: str) -> list[float]:
        lowered = text.lower()
        values = [
            float(lowered.count("alpha")),
            float(lowered.count("beta")),
            float(lowered.count("gamma")),
            1.0,
        ]
        norm = math.sqrt(sum(value * value for value in values))
        return [value / norm for value in values]


class MemoryVectorStore(VectorStore):
    def __init__(self) -> None:
        self.dimension: int | None = None
        self.items: list[tuple[Chunk, list[float]]] = []

    async def ensure_collection(self, dimension: int) -> None:
        if self.dimension is not None and self.dimension != dimension:
            raise ValueError("dimension mismatch")
        self.dimension = dimension

    async def upsert(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        self.items.extend(zip(chunks, vectors, strict=True))

    async def search(self, vector: list[float], top_k: int) -> list[RetrievedChunk]:
        scored = [
            (sum(left * right for left, right in zip(stored, vector, strict=True)), chunk)
            for chunk, stored in self.items
        ]
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            RetrievedChunk(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                text=chunk.text,
                score=score,
                metadata=chunk.metadata,
            )
            for score, chunk in scored[:top_k]
        ]

    async def close(self) -> None:
        return None


class FakeLLMProvider(LLMProvider):
    def __init__(self, answer: str = "Answer based on context.") -> None:
        self.answer = answer
        self.calls: list[tuple[str, str]] = []

    async def generate(self, prompt: str, *, system_prompt: str) -> GenerationResult:
        self.calls.append((prompt, system_prompt))
        return GenerationResult(
            text=self.answer,
            model="fake-model",
            input_tokens=12,
            output_tokens=5,
        )
