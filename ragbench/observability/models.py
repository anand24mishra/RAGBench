from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RetrievalObservation(BaseModel):
    model_config = ConfigDict(frozen=True)

    document_ids: list[str] = Field(default_factory=list)
    chunk_ids: list[str] = Field(default_factory=list)
    scores: list[float] = Field(default_factory=list)
    count: int = Field(ge=0)
    embedding_ms: float = Field(ge=0.0)
    search_ms: float = Field(ge=0.0)


class GenerationObservation(BaseModel):
    model_config = ConfigDict(frozen=True)

    model: str | None = None
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    generation_ms: float = Field(ge=0.0)


class TimingObservation(BaseModel):
    model_config = ConfigDict(frozen=True)

    embedding_ms: float = Field(ge=0.0)
    retrieval_ms: float = Field(ge=0.0)
    generation_ms: float = Field(ge=0.0)
    total_ms: float = Field(ge=0.0)


class RequestObservation(BaseModel):
    model_config = ConfigDict(frozen=True)

    request_id: str
    experiment_id: str | None = None
    query_id: str | None = None
    embedding_model: str | None = None
    generation_model: str | None = None
    retrieval: RetrievalObservation | None = None
    generation: GenerationObservation | None = None
    timing: TimingObservation | None = None
    outcome: Literal["success", "error"] = "success"
    error_code: str | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
