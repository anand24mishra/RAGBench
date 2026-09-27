from __future__ import annotations

import uuid
from typing import Any

from qdrant_client import AsyncQdrantClient, models

from ragbench.app.domain.errors import VectorStoreError
from ragbench.app.domain.models import Chunk, RetrievedChunk
from ragbench.app.vector_store.base import VectorStore


class QdrantVectorStore(VectorStore):
    def __init__(
        self,
        url: str | None,
        collection_name: str,
        *,
        client: AsyncQdrantClient | None = None,
    ) -> None:
        self.collection_name = collection_name
        if client is not None:
            self._client = client
        elif url in ("memory", ":memory:"):
            self._client = AsyncQdrantClient(location=":memory:")
        else:
            self._client = AsyncQdrantClient(url=url)

    async def ensure_collection(self, dimension: int) -> None:
        try:
            exists = await self._client.collection_exists(self.collection_name)
            if not exists:
                await self._client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=dimension,
                        distance=models.Distance.COSINE,
                    ),
                )
                return
            collection = await self._client.get_collection(self.collection_name)
            vectors_config: Any = collection.config.params.vectors
            existing_dimension = getattr(vectors_config, "size", None)
            if existing_dimension is not None and existing_dimension != dimension:
                raise VectorStoreError(
                    "Existing Qdrant collection dimension does not match the embedding model"
                )
        except VectorStoreError:
            raise
        except Exception as exc:
            raise VectorStoreError("Failed to create or inspect the Qdrant collection") from exc

    async def upsert(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        if len(chunks) != len(vectors):
            raise VectorStoreError("Chunk and vector counts do not match")
        if not chunks:
            return
        points = [
            models.PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, chunk.chunk_id)),
                vector=vector,
                payload={
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "text": chunk.text,
                    "metadata": chunk.metadata,
                },
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        try:
            await self._client.upsert(
                collection_name=self.collection_name,
                points=points,
                wait=True,
            )
        except Exception as exc:
            raise VectorStoreError("Failed to upsert chunks into Qdrant") from exc

    async def search(self, vector: list[float], top_k: int) -> list[RetrievedChunk]:
        try:
            response = await self._client.query_points(
                collection_name=self.collection_name,
                query=vector,
                limit=top_k,
                with_payload=True,
            )
        except Exception as exc:
            raise VectorStoreError("Qdrant vector search failed") from exc

        results: list[RetrievedChunk] = []
        for point in response.points:
            payload = point.payload or {}
            try:
                results.append(
                    RetrievedChunk(
                        chunk_id=str(payload["chunk_id"]),
                        document_id=str(payload["document_id"]),
                        text=str(payload["text"]),
                        score=float(point.score),
                        metadata=dict(payload.get("metadata") or {}),
                    )
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise VectorStoreError("Qdrant returned an invalid chunk payload") from exc
        return results

    async def close(self) -> None:
        await self._client.close()
