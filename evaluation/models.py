from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from benchmarks.timing import ExperimentTimingResult
from ragbench.cost.models import CostAccountingResult


class RetrievedDocumentResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    rank: int = Field(ge=1)
    document_id: str
    raw_document_id: str
    chunk_id: str
    score: float


class QueryEvaluationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    query_id: str
    question: str
    relevant_documents: list[str]
    retrieved: list[RetrievedDocumentResult]
    retrieved_documents: list[str]
    recall_at_1: float = Field(ge=0, le=1)
    recall_at_3: float = Field(ge=0, le=1)
    recall_at_5: float = Field(ge=0, le=1)
    reciprocal_rank: float = Field(ge=0, le=1)
    embedding_ms: float | None = None
    retrieval_ms: float | None = None
    candidate_count: int | None = None
    context: str | None = None
    generated_answer: str | None = None
    reference_answer: str | None = None
    generation_metrics: GenerationMetrics | None = None
    generation_ms: float | None = None
    total_ms: float | None = None
    failure_classification: GenerationFailureType | None = None
    generation_details: dict[str, Any] | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    input_cost: float | None = None
    output_cost: float | None = None
    total_cost: float | None = None
    cost_status: Literal["available", "unavailable"] = "unavailable"


class ReliabilityMetrics(BaseModel):
    model_config = ConfigDict(frozen=True)

    total_requests: int = Field(ge=0)
    successful_requests: int = Field(ge=0)
    failed_requests: int = Field(ge=0)
    failure_rate: float = Field(ge=0.0, le=1.0)
    failure_categories: dict[str, int] = Field(default_factory=dict)
    timeouts: int = Field(default=0, ge=0)
    provider_errors: int = Field(default=0, ge=0)


class RetrievalFailure(BaseModel):
    model_config = ConfigDict(frozen=True)

    query_id: str
    expected_document: str
    retrieved_documents: list[str]
    retrieval_scores: list[float]


GenerationFailureType = Literal[
    "retrieval_failure",
    "context_failure",
    "generation_failure",
    "grounding_failure",
    "provider_failure",
]


class GenerationMetrics(BaseModel):
    model_config = ConfigDict(frozen=True)

    correctness: float = Field(ge=0.0, le=1.0)
    faithfulness: float = Field(ge=0.0, le=1.0)
    context_relevance: float = Field(ge=0.0, le=1.0)


class GenerationFailure(BaseModel):
    model_config = ConfigDict(frozen=True)

    query_id: str
    failure_type: GenerationFailureType
    expected_evidence: list[str]
    retrieved_evidence: list[str]
    answer: str
    reference: str | None = None
    failed_metric: str
    reason: str


class RetrieverConfiguration(BaseModel):
    model_config = ConfigDict(frozen=True)

    chunk_size: int
    chunk_overlap: int
    embedding_batch_size: int
    distance: Literal["cosine"] = "cosine"
    vector_store: Literal["qdrant"] = "qdrant"
    qdrant_mode: Literal["memory", "remote"]
    normalized_embeddings: bool = True


class GenerationEvaluationStatus(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["not_implemented", "evaluated"] = "not_implemented"
    metrics: list[str] = Field(default_factory=list)
    evaluator_type: str | None = None
    generation_model: str | None = None
    judge_model: str | None = None
    aggregate_metrics: dict[str, float] = Field(default_factory=dict)


class EvaluationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: Literal["1", "3", "4", "5"] = "1"
    experiment_id: str
    timestamp: datetime
    dataset_name: str
    dataset_version: str
    dataset_fingerprint: str
    corpus_documents: dict[str, str]
    retriever_configuration: RetrieverConfiguration
    embedding_model: str
    software_versions: dict[str, str]
    top_k: int = Field(ge=1)
    query_count: int = Field(ge=1)
    metrics: dict[str, float]
    queries: list[QueryEvaluationResult]
    failures: list[RetrievalFailure]
    generation_evaluation: GenerationEvaluationStatus = Field(
        default_factory=GenerationEvaluationStatus
    )
    embedding_dimension: int | None = None
    hypothesis: str | None = None
    changed_parameter: str | None = None
    timing: ExperimentTimingResult | None = None
    candidate_count: int | None = None
    interpretation: str | None = None
    decision: str | None = None
    generation_model: str | None = None
    judge_model: str | None = None
    evaluator_type: str | None = None
    generation_failures: list[GenerationFailure] = Field(default_factory=list)
    dataset_question_count: int | None = None
    dataset_document_count: int | None = None
    corpus_fingerprint: str | None = None
    cost_accounting: CostAccountingResult | None = None
    reliability: ReliabilityMetrics | None = None


class RankingChange(BaseModel):
    model_config = ConfigDict(frozen=True)

    query_id: str
    expected_document: str
    baseline_rank: int | None = None
    experiment_rank: int | None = None
    baseline_score: float | None = None
    experiment_score: float | None = None


class MetricComparison(BaseModel):
    model_config = ConfigDict(frozen=True)

    baseline: float
    experiment: float
    delta: float


class ComparisonResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    baseline_experiment_id: str
    experiment_id: str
    dataset_version: str
    metrics: dict[str, MetricComparison]
    latency_metrics: dict[str, MetricComparison] = Field(default_factory=dict)
    generation_metrics: dict[str, MetricComparison] = Field(default_factory=dict)
    cost_metrics: dict[str, MetricComparison] = Field(default_factory=dict)
    reliability_metrics: dict[str, MetricComparison] = Field(default_factory=dict)
    ranking_changes: list[RankingChange] = Field(default_factory=list)
    changed_parameter: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
