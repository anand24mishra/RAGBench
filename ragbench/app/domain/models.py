from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Document(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    text: str
    metadata: dict[str, Any]


class Chunk(BaseModel):
    model_config = ConfigDict(frozen=True)

    chunk_id: str
    document_id: str
    text: str
    metadata: dict[str, Any]


class RetrievedChunk(BaseModel):
    model_config = ConfigDict(frozen=True)

    chunk_id: str
    document_id: str
    text: str
    score: float
    metadata: dict[str, Any]


class RetrievalResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    chunks: list[RetrievedChunk]
    embedding_ms: float = Field(ge=0)
    search_ms: float = Field(ge=0)
