from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from evaluation.models import EvaluationResult


class ModelTradeoffResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    config_name: str
    model_name: str
    correctness: float | None = None
    faithfulness: float | None = None
    context_relevance: float | None = None
    mean_latency_ms: float = Field(ge=0.0)
    p95_latency_ms: float = Field(ge=0.0)
    total_tokens: int | None = None
    cost_per_query: float | None = None
    total_cost: float | None = None


class CostVsQualityComparison(BaseModel):
    model_config = ConfigDict(frozen=True)

    experiment_id: str
    timestamp: datetime
    config_a: ModelTradeoffResult
    config_b: ModelTradeoffResult
    delta_correctness: float | None = None
    delta_cost_per_query: float | None = None
    delta_mean_latency_ms: float | None = None
    tradeoff_analysis: str


def compare_cost_vs_quality(
    result_a: EvaluationResult,
    result_b: EvaluationResult,
    name_a: str = "Config A (Lower Cost)",
    name_b: str = "Config B (Higher Cost)",
    experiment_id: str = "cost-vs-quality",
) -> CostVsQualityComparison:
    """Compares two evaluated model configurations across quality, latency, tokens, and cost.

    Exposes the Pareto trade-off between cheaper/faster models and higher quality models.
    """

    def _extract(res: EvaluationResult, name: str) -> ModelTradeoffResult:
        gen = res.generation_evaluation.aggregate_metrics
        correctness = gen.get("correctness")
        faithfulness = gen.get("faithfulness")
        context_relevance = gen.get("context_relevance")

        mean_lat = 0.0
        p95_lat = 0.0
        if res.timing is not None:
            if res.timing.generation_latency is not None:
                mean_lat = res.timing.generation_latency.mean_ms
                p95_lat = res.timing.generation_latency.p95_ms
            else:
                mean_lat = res.timing.retrieval_latency.mean_ms
                p95_lat = res.timing.retrieval_latency.p95_ms

        total_tokens = None
        cpq = None
        total_cost = None
        if res.cost_accounting is not None and res.cost_accounting.cost_status == "available":
            total_tokens = res.cost_accounting.total_tokens
            cpq = res.cost_accounting.cost_per_query
            total_cost = res.cost_accounting.total_cost

        model_name = (
            res.generation_model
            or res.generation_evaluation.generation_model
            or res.embedding_model
        )

        return ModelTradeoffResult(
            config_name=name,
            model_name=model_name,
            correctness=correctness,
            faithfulness=faithfulness,
            context_relevance=context_relevance,
            mean_latency_ms=round(mean_lat, 2),
            p95_latency_ms=round(p95_lat, 2),
            total_tokens=total_tokens,
            cost_per_query=cpq,
            total_cost=total_cost,
        )

    t_a = _extract(result_a, name_a)
    t_b = _extract(result_b, name_b)

    delta_corr = (
        round(t_b.correctness - t_a.correctness, 4)
        if t_a.correctness is not None and t_b.correctness is not None
        else None
    )
    delta_cost = (
        round(t_b.cost_per_query - t_a.cost_per_query, 6)
        if t_a.cost_per_query is not None and t_b.cost_per_query is not None
        else None
    )
    delta_lat = round(t_b.mean_latency_ms - t_a.mean_latency_ms, 2)

    # Construct analysis
    analysis_parts = []
    if delta_corr is not None:
        analysis_parts.append(
            f"Quality delta (correctness): {delta_corr:+.2%} ({t_a.config_name}: "
            f"{t_a.correctness:.2f} vs {t_b.config_name}: {t_b.correctness:.2f})"
        )
    if delta_cost is not None and t_a.cost_per_query and t_a.cost_per_query > 0:
        cost_ratio = (
            t_b.cost_per_query / t_a.cost_per_query if t_b.cost_per_query is not None else 1.0
        )
        analysis_parts.append(
            f"Cost ratio: {cost_ratio:.2f}x ({t_a.config_name} ${t_a.cost_per_query:.6f} "
            f"vs {t_b.config_name} ${t_b.cost_per_query:.6f}/query)"
        )
    analysis_parts.append(
        f"Mean latency delta: {delta_lat:+.2f} ms ({t_a.mean_latency_ms:.2f} ms "
        f"vs {t_b.mean_latency_ms:.2f} ms)"
    )

    tradeoff_text = " | ".join(analysis_parts)

    return CostVsQualityComparison(
        experiment_id=experiment_id,
        timestamp=datetime.now(UTC),
        config_a=t_a,
        config_b=t_b,
        delta_correctness=delta_corr,
        delta_cost_per_query=delta_cost,
        delta_mean_latency_ms=delta_lat,
        tradeoff_analysis=tradeoff_text,
    )
