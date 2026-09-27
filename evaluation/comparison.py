from __future__ import annotations

import json
from pathlib import Path

from evaluation.models import (
    ComparisonResult,
    EvaluationResult,
    MetricComparison,
    RankingChange,
)


class ComparisonError(ValueError):
    """Raised when two evaluation results are not comparable."""


def load_evaluation_result(path: Path) -> EvaluationResult:
    try:
        return EvaluationResult.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ComparisonError(f"Invalid evaluation result: {path}") from exc


def find_ranking_changes(
    baseline: EvaluationResult,
    experiment: EvaluationResult,
) -> list[RankingChange]:
    ranking_changes: list[RankingChange] = []
    exp_queries = {q.query_id: q for q in experiment.queries}

    for base_q in baseline.queries:
        exp_q = exp_queries.get(base_q.query_id)
        if not exp_q:
            continue

        for expected_doc in base_q.relevant_documents:
            base_rank: int | None = None
            base_score: float | None = None
            for item in base_q.retrieved:
                if item.document_id == expected_doc:
                    base_rank = item.rank
                    base_score = item.score
                    break

            exp_rank: int | None = None
            exp_score: float | None = None
            for item in exp_q.retrieved:
                if item.document_id == expected_doc:
                    exp_rank = item.rank
                    exp_score = item.score
                    break

            if base_rank != exp_rank:
                ranking_changes.append(
                    RankingChange(
                        query_id=base_q.query_id,
                        expected_document=expected_doc,
                        baseline_rank=base_rank,
                        experiment_rank=exp_rank,
                        baseline_score=base_score,
                        experiment_score=exp_score,
                    )
                )

    return ranking_changes


def compare_results(
    baseline: EvaluationResult,
    experiment: EvaluationResult,
) -> ComparisonResult:
    if baseline.dataset_version != experiment.dataset_version:
        raise ComparisonError("Cannot compare results from different dataset versions")
    if baseline.dataset_fingerprint != experiment.dataset_fingerprint:
        raise ComparisonError("Cannot compare results with different dataset fingerprints")
    if baseline.query_count != experiment.query_count:
        raise ComparisonError("Cannot compare results with different query counts")
    if set(baseline.metrics) != set(experiment.metrics):
        raise ComparisonError("Cannot compare results with different metric sets")

    metrics = {
        name: MetricComparison(
            baseline=baseline.metrics[name],
            experiment=experiment.metrics[name],
            delta=experiment.metrics[name] - baseline.metrics[name],
        )
        for name in sorted(baseline.metrics)
    }

    latency_metrics: dict[str, MetricComparison] = {}
    if baseline.timing is not None and experiment.timing is not None:
        b_timing = baseline.timing
        e_timing = experiment.timing
        pairs = [
            (
                "mean_embedding_ms",
                b_timing.embedding_latency.mean_ms,
                e_timing.embedding_latency.mean_ms,
            ),
            (
                "p50_embedding_ms",
                b_timing.embedding_latency.p50_ms,
                e_timing.embedding_latency.p50_ms,
            ),
            (
                "p95_embedding_ms",
                b_timing.embedding_latency.p95_ms,
                e_timing.embedding_latency.p95_ms,
            ),
            (
                "mean_retrieval_ms",
                b_timing.retrieval_latency.mean_ms,
                e_timing.retrieval_latency.mean_ms,
            ),
            (
                "p50_retrieval_ms",
                b_timing.retrieval_latency.p50_ms,
                e_timing.retrieval_latency.p50_ms,
            ),
            (
                "p95_retrieval_ms",
                b_timing.retrieval_latency.p95_ms,
                e_timing.retrieval_latency.p95_ms,
            ),
            ("total_runtime_ms", b_timing.total_runtime_ms, e_timing.total_runtime_ms),
        ]
        if b_timing.generation_latency is not None and e_timing.generation_latency is not None:
            pairs.extend(
                [
                    (
                        "mean_generation_ms",
                        b_timing.generation_latency.mean_ms,
                        e_timing.generation_latency.mean_ms,
                    ),
                    (
                        "p50_generation_ms",
                        b_timing.generation_latency.p50_ms,
                        e_timing.generation_latency.p50_ms,
                    ),
                    (
                        "p95_generation_ms",
                        b_timing.generation_latency.p95_ms,
                        e_timing.generation_latency.p95_ms,
                    ),
                ]
            )
        for name, b_val, e_val in pairs:
            latency_metrics[name] = MetricComparison(
                baseline=b_val, experiment=e_val, delta=e_val - b_val
            )

    generation_metrics: dict[str, MetricComparison] = {}
    b_gen = baseline.generation_evaluation.aggregate_metrics
    e_gen = experiment.generation_evaluation.aggregate_metrics
    if b_gen and e_gen:
        for name in sorted(set(b_gen) & set(e_gen)):
            generation_metrics[name] = MetricComparison(
                baseline=b_gen[name],
                experiment=e_gen[name],
                delta=e_gen[name] - b_gen[name],
            )

    cost_metrics: dict[str, MetricComparison] = {}
    if (
        baseline.cost_accounting is not None
        and experiment.cost_accounting is not None
        and baseline.cost_accounting.cost_status == "available"
        and experiment.cost_accounting.cost_status == "available"
    ):
        b_c = baseline.cost_accounting
        e_c = experiment.cost_accounting
        if b_c.cost_per_query is not None and e_c.cost_per_query is not None:
            cost_metrics["cost_per_query"] = MetricComparison(
                baseline=b_c.cost_per_query,
                experiment=e_c.cost_per_query,
                delta=round(e_c.cost_per_query - b_c.cost_per_query, 6),
            )
        if b_c.total_cost is not None and e_c.total_cost is not None:
            cost_metrics["total_cost"] = MetricComparison(
                baseline=b_c.total_cost,
                experiment=e_c.total_cost,
                delta=round(e_c.total_cost - b_c.total_cost, 6),
            )

    reliability_metrics: dict[str, MetricComparison] = {}
    if baseline.reliability is not None and experiment.reliability is not None:
        b_r = baseline.reliability
        e_r = experiment.reliability
        reliability_metrics["failure_rate"] = MetricComparison(
            baseline=b_r.failure_rate,
            experiment=e_r.failure_rate,
            delta=round(e_r.failure_rate - b_r.failure_rate, 4),
        )
        reliability_metrics["timeouts"] = MetricComparison(
            baseline=float(b_r.timeouts),
            experiment=float(e_r.timeouts),
            delta=float(e_r.timeouts - b_r.timeouts),
        )

    ranking_changes = find_ranking_changes(baseline, experiment)

    return ComparisonResult(
        baseline_experiment_id=baseline.experiment_id,
        experiment_id=experiment.experiment_id,
        dataset_version=baseline.dataset_version,
        metrics=metrics,
        latency_metrics=latency_metrics,
        generation_metrics=generation_metrics,
        cost_metrics=cost_metrics,
        reliability_metrics=reliability_metrics,
        ranking_changes=ranking_changes,
        changed_parameter=experiment.changed_parameter,
    )


def write_comparison(result: ComparisonResult, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
