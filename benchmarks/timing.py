from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from pydantic import BaseModel, ConfigDict, Field


class LatencyStats(BaseModel):
    model_config = ConfigDict(frozen=True)

    sample_size: int = Field(ge=1)
    mean_ms: float = Field(ge=0)
    p50_ms: float = Field(ge=0)
    p95_ms: float = Field(ge=0)
    p99_ms: float = Field(ge=0)
    min_ms: float = Field(ge=0)
    max_ms: float = Field(ge=0)


class QueryLatency(BaseModel):
    model_config = ConfigDict(frozen=True)

    query_id: str
    embedding_ms: float = Field(ge=0)
    retrieval_ms: float = Field(ge=0)
    generation_ms: float = Field(default=0.0, ge=0)
    total_ms: float = Field(ge=0)


class ExperimentTimingResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    sample_size: int = Field(ge=0)
    embedding_latency: LatencyStats
    retrieval_latency: LatencyStats
    generation_latency: LatencyStats | None = None
    total_runtime_ms: float = Field(ge=0)
    query_latencies: list[QueryLatency] = Field(default_factory=list)


def calculate_latency_stats(latencies: Sequence[float]) -> LatencyStats:
    if not latencies:
        raise ValueError("Cannot calculate latency statistics for an empty sequence")

    arr = np.asarray(latencies, dtype=float)
    return LatencyStats(
        sample_size=len(arr),
        mean_ms=float(np.mean(arr)),
        p50_ms=float(np.percentile(arr, 50)),
        p95_ms=float(np.percentile(arr, 95)),
        p99_ms=float(np.percentile(arr, 99)),
        min_ms=float(np.min(arr)),
        max_ms=float(np.max(arr)),
    )
