from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

CheckStatus = Literal["pass", "fail", "inconclusive"]


class QualityThresholds(BaseModel):
    model_config = ConfigDict(frozen=True)

    recall_at_1_min_delta: float = Field(default=-0.05)
    recall_at_3_min_delta: float = Field(default=-0.05)
    recall_at_5_min_delta: float = Field(default=-0.02)
    mrr_min_delta: float = Field(default=-0.02)
    correctness_min_delta: float = Field(default=-0.05)
    faithfulness_min_delta: float = Field(default=-0.05)
    context_relevance_min_delta: float = Field(default=-0.05)


class LatencyThresholds(BaseModel):
    model_config = ConfigDict(frozen=True)

    p95_max_relative_increase: float = Field(default=0.25)  # +25% allowed
    mean_max_relative_increase: float = Field(default=0.30)  # +30% allowed


class CostThresholds(BaseModel):
    model_config = ConfigDict(frozen=True)

    max_relative_increase: float = Field(default=0.30)  # +30% cost increase allowed


class ReliabilityThresholds(BaseModel):
    model_config = ConfigDict(frozen=True)

    max_failure_rate: float = Field(default=0.05)  # 5% max failure rate
    max_timeouts: int = Field(default=0)


class RegressionPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)

    policy_name: str = "default_ragbench_policy"
    quality: QualityThresholds = Field(default_factory=QualityThresholds)
    latency: LatencyThresholds = Field(default_factory=LatencyThresholds)
    cost: CostThresholds = Field(default_factory=CostThresholds)
    reliability: ReliabilityThresholds = Field(default_factory=ReliabilityThresholds)
    require_matching_dataset_version: bool = True
    require_matching_dataset_fingerprint: bool = True


class RegressionCheck(BaseModel):
    model_config = ConfigDict(frozen=True)

    category: Literal["quality", "latency", "cost", "reliability", "dataset"]
    metric: str
    baseline: float | str | None = None
    candidate: float | str | None = None
    delta: float | None = None
    threshold: float | str | None = None
    status: CheckStatus
    message: str


class QueryRegressionDiagnostic(BaseModel):
    model_config = ConfigDict(frozen=True)

    query_id: str
    question: str
    relevant_documents: list[str] = Field(default_factory=list)
    baseline_rank: int | None = None
    candidate_rank: int | None = None
    baseline_metrics: dict[str, float] = Field(default_factory=dict)
    candidate_metrics: dict[str, float] = Field(default_factory=dict)
    baseline_answer: str | None = None
    candidate_answer: str | None = None
    reference_answer: str | None = None
    retrieved_documents: list[str] = Field(default_factory=list)
    reason: str


class RegressionDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: CheckStatus
    baseline_id: str
    candidate_id: str
    dataset_version: str
    checks: list[RegressionCheck] = Field(default_factory=list)
    diagnostics: list[QueryRegressionDiagnostic] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)
