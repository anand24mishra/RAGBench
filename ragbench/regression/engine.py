from __future__ import annotations

from typing import Any

from evaluation.models import EvaluationResult
from ragbench.regression.models import (
    CheckStatus,
    QueryRegressionDiagnostic,
    RegressionCheck,
    RegressionDecision,
    RegressionPolicy,
)


def evaluate_regression(
    baseline: EvaluationResult,
    candidate: EvaluationResult,
    policy: RegressionPolicy | None = None,
) -> RegressionDecision:
    resolved_policy = policy or RegressionPolicy()
    checks: list[RegressionCheck] = []
    warnings: list[str] = []
    diagnostics: list[QueryRegressionDiagnostic] = []

    # 1. Dataset compatibility check
    dataset_version_match = baseline.dataset_version == candidate.dataset_version
    dataset_fingerprint_match = baseline.dataset_fingerprint == candidate.dataset_fingerprint

    if not dataset_version_match:
        msg = (
            f"Dataset version mismatch: baseline '{baseline.dataset_version}' vs "
            f"candidate '{candidate.dataset_version}'"
        )
        warnings.append(msg)
        checks.append(
            RegressionCheck(
                category="dataset",
                metric="dataset_version",
                baseline=baseline.dataset_version,
                candidate=candidate.dataset_version,
                status="inconclusive"
                if resolved_policy.require_matching_dataset_version
                else "pass",
                message=msg,
            )
        )

    if not dataset_fingerprint_match:
        msg = (
            f"Dataset fingerprint mismatch: baseline '{baseline.dataset_fingerprint[:8]}' vs "
            f"candidate '{candidate.dataset_fingerprint[:8]}'"
        )
        warnings.append(msg)
        checks.append(
            RegressionCheck(
                category="dataset",
                metric="dataset_fingerprint",
                baseline=baseline.dataset_fingerprint[:8],
                candidate=candidate.dataset_fingerprint[:8],
                status="inconclusive"
                if resolved_policy.require_matching_dataset_fingerprint
                else "pass",
                message=msg,
            )
        )

    # 2. Retrieval quality checks
    retrieval_metrics = ["recall_at_1", "recall_at_3", "recall_at_5", "mrr"]
    for m in retrieval_metrics:
        b_val = baseline.metrics.get(m)
        c_val = candidate.metrics.get(m)
        threshold = getattr(resolved_policy.quality, f"{m}_min_delta")

        if b_val is not None and c_val is not None:
            delta = round(c_val - b_val, 6)
            passed = delta >= threshold
            checks.append(
                RegressionCheck(
                    category="quality",
                    metric=m,
                    baseline=round(b_val, 6),
                    candidate=round(c_val, 6),
                    delta=delta,
                    threshold=threshold,
                    status="pass" if passed else "fail",
                    message=(
                        f"{m} delta {delta:+.4f} >= threshold {threshold:+.4f}"
                        if passed
                        else f"{m} regressed: delta {delta:+.4f} < threshold {threshold:+.4f}"
                    ),
                )
            )
        else:
            checks.append(
                RegressionCheck(
                    category="quality",
                    metric=m,
                    baseline=b_val,
                    candidate=c_val,
                    status="inconclusive",
                    message=f"{m} measurement unavailable in baseline or candidate",
                )
            )

    # 3. Generation quality checks
    b_gen = baseline.generation_evaluation.aggregate_metrics
    c_gen = candidate.generation_evaluation.aggregate_metrics
    gen_metrics = ["correctness", "faithfulness", "context_relevance"]

    for m in gen_metrics:
        b_val = b_gen.get(m) if b_gen else None
        c_val = c_gen.get(m) if c_gen else None
        threshold = getattr(resolved_policy.quality, f"{m}_min_delta")

        if b_val is not None and c_val is not None:
            delta = round(c_val - b_val, 6)
            passed = delta >= threshold
            checks.append(
                RegressionCheck(
                    category="quality",
                    metric=m,
                    baseline=round(b_val, 6),
                    candidate=round(c_val, 6),
                    delta=delta,
                    threshold=threshold,
                    status="pass" if passed else "fail",
                    message=(
                        f"{m} delta {delta:+.4f} >= threshold {threshold:+.4f}"
                        if passed
                        else f"{m} regressed: delta {delta:+.4f} < threshold {threshold:+.4f}"
                    ),
                )
            )
        elif b_val is None and c_val is None:
            # Neither evaluated generation - skip check without failing
            pass
        else:
            checks.append(
                RegressionCheck(
                    category="quality",
                    metric=m,
                    baseline=b_val,
                    candidate=c_val,
                    status="inconclusive",
                    message=f"Generation metric '{m}' unavailable in baseline or candidate",
                )
            )

    # 4. Latency checks
    if baseline.timing is not None and candidate.timing is not None:
        b_p95 = baseline.timing.retrieval_latency.p95_ms
        c_p95 = candidate.timing.retrieval_latency.p95_ms
        rel_p95_inc = (c_p95 - b_p95) / b_p95 if b_p95 > 0 else 0.0
        p95_threshold = resolved_policy.latency.p95_max_relative_increase
        p95_passed = rel_p95_inc <= p95_threshold

        checks.append(
            RegressionCheck(
                category="latency",
                metric="retrieval_p95_ms",
                baseline=round(b_p95, 3),
                candidate=round(c_p95, 3),
                delta=round(c_p95 - b_p95, 3),
                threshold=round(p95_threshold, 3),
                status="pass" if p95_passed else "fail",
                message=(
                    f"Retrieval P95 relative increase {rel_p95_inc:+.2%} <= {p95_threshold:+.2%}"
                    if p95_passed
                    else (
                        f"Retrieval P95 latency regressed: {rel_p95_inc:+.2%} > "
                        f"{p95_threshold:+.2%}"
                    )
                ),
            )
        )
    else:
        # Latency check inconclusive if timing absent
        pass

    # 5. Cost checks
    b_cost = baseline.cost_accounting
    c_cost = candidate.cost_accounting
    if (
        b_cost is not None
        and c_cost is not None
        and b_cost.cost_status == "available"
        and c_cost.cost_status == "available"
        and b_cost.cost_per_query is not None
        and c_cost.cost_per_query is not None
    ):
        b_cpq = b_cost.cost_per_query
        c_cpq = c_cost.cost_per_query
        rel_inc = (c_cpq - b_cpq) / b_cpq if b_cpq > 0 else 0.0
        cost_threshold = resolved_policy.cost.max_relative_increase
        cost_passed = rel_inc <= cost_threshold
        checks.append(
            RegressionCheck(
                category="cost",
                metric="cost_per_query",
                baseline=round(b_cpq, 6),
                candidate=round(c_cpq, 6),
                delta=round(c_cpq - b_cpq, 6),
                threshold=round(cost_threshold, 3),
                status="pass" if cost_passed else "fail",
                message=(
                    f"Cost per query relative change {rel_inc:+.2%} <= {cost_threshold:+.2%}"
                    if cost_passed
                    else f"Cost per query regressed: {rel_inc:+.2%} > {cost_threshold:+.2%}"
                ),
            )
        )
    elif b_cost is not None or c_cost is not None:
        checks.append(
            RegressionCheck(
                category="cost",
                metric="cost_per_query",
                status="inconclusive",
                message="Cost accounting unavailable in baseline or candidate",
            )
        )

    # 6. Reliability checks
    if candidate.reliability is not None:
        rel = candidate.reliability
        fail_rate_pass = rel.failure_rate <= resolved_policy.reliability.max_failure_rate
        checks.append(
            RegressionCheck(
                category="reliability",
                metric="failure_rate",
                candidate=round(rel.failure_rate, 4),
                threshold=round(resolved_policy.reliability.max_failure_rate, 4),
                status="pass" if fail_rate_pass else "fail",
                message=(
                    f"Candidate failure rate {rel.failure_rate:.2%} <= threshold "
                    f"{resolved_policy.reliability.max_failure_rate:.2%}"
                    if fail_rate_pass
                    else f"Candidate failure rate {rel.failure_rate:.2%} exceeded threshold "
                    f"{resolved_policy.reliability.max_failure_rate:.2%}"
                ),
            )
        )
        timeout_pass = rel.timeouts <= resolved_policy.reliability.max_timeouts
        checks.append(
            RegressionCheck(
                category="reliability",
                metric="timeouts",
                candidate=float(rel.timeouts),
                threshold=float(resolved_policy.reliability.max_timeouts),
                status="pass" if timeout_pass else "fail",
                message=(
                    f"Timeouts {rel.timeouts} <= {resolved_policy.reliability.max_timeouts}"
                    if timeout_pass
                    else f"Timeouts {rel.timeouts} > {resolved_policy.reliability.max_timeouts}"
                ),
            )
        )

    # 7. Per-query diagnostics for regressed queries
    b_queries = {q.query_id: q for q in baseline.queries}
    for c_q in candidate.queries:
        b_q = b_queries.get(c_q.query_id)
        if not b_q:
            continue
        reasons: list[str] = []
        if c_q.reciprocal_rank < b_q.reciprocal_rank:
            reasons.append(
                f"Reciprocal rank dropped from {b_q.reciprocal_rank:.3f} "
                f"to {c_q.reciprocal_rank:.3f}"
            )
        if b_q.generation_metrics and c_q.generation_metrics:
            if c_q.generation_metrics.correctness < b_q.generation_metrics.correctness:
                reasons.append(
                    f"Correctness dropped from {b_q.generation_metrics.correctness:.2f} "
                    f"to {c_q.generation_metrics.correctness:.2f}"
                )
            if c_q.generation_metrics.faithfulness < b_q.generation_metrics.faithfulness:
                reasons.append(
                    f"Faithfulness dropped from {b_q.generation_metrics.faithfulness:.2f} "
                    f"to {c_q.generation_metrics.faithfulness:.2f}"
                )
        if c_q.failure_classification is not None and b_q.failure_classification is None:
            reasons.append(f"Candidate encountered {c_q.failure_classification}")

        if reasons:
            b_m: dict[str, float] = {
                "rr": b_q.reciprocal_rank,
                "r@1": b_q.recall_at_1,
                "r@5": b_q.recall_at_5,
            }
            if b_q.generation_metrics:
                b_m["correctness"] = b_q.generation_metrics.correctness
                b_m["faithfulness"] = b_q.generation_metrics.faithfulness
            c_m: dict[str, float] = {
                "rr": c_q.reciprocal_rank,
                "r@1": c_q.recall_at_1,
                "r@5": c_q.recall_at_5,
            }
            if c_q.generation_metrics:
                c_m["correctness"] = c_q.generation_metrics.correctness
                c_m["faithfulness"] = c_q.generation_metrics.faithfulness

            diagnostics.append(
                QueryRegressionDiagnostic(
                    query_id=c_q.query_id,
                    question=c_q.question,
                    relevant_documents=c_q.relevant_documents,
                    baseline_metrics=b_m,
                    candidate_metrics=c_m,
                    baseline_answer=b_q.generated_answer,
                    candidate_answer=c_q.generated_answer,
                    reference_answer=c_q.reference_answer,
                    retrieved_documents=c_q.retrieved_documents,
                    reason="; ".join(reasons),
                )
            )

    # 8. Determine overall status
    overall_status: CheckStatus
    if any(c.status == "fail" for c in checks):
        overall_status = "fail"
    elif any(c.status == "inconclusive" for c in checks):
        overall_status = "inconclusive"
    else:
        overall_status = "pass"

    summary = (
        f"Regression check {overall_status.upper()}: "
        f"{sum(1 for c in checks if c.status == 'pass')} passed, "
        f"{sum(1 for c in checks if c.status == 'fail')} failed, "
        f"{sum(1 for c in checks if c.status == 'inconclusive')} inconclusive. "
        f"Regressed queries: {len(diagnostics)}."
    )

    metadata: dict[str, Any] = {
        "policy_name": resolved_policy.policy_name,
        "baseline_model": baseline.embedding_model,
        "candidate_model": candidate.embedding_model,
        "baseline_query_count": baseline.query_count,
        "candidate_query_count": candidate.query_count,
    }

    return RegressionDecision(
        status=overall_status,
        baseline_id=baseline.experiment_id,
        candidate_id=candidate.experiment_id,
        dataset_version=candidate.dataset_version,
        checks=checks,
        diagnostics=diagnostics,
        warnings=warnings,
        summary=summary,
        metadata=metadata,
    )
