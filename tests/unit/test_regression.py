from __future__ import annotations

from datetime import UTC, datetime

from evaluation.models import (
    EvaluationResult,
    GenerationEvaluationStatus,
    ReliabilityMetrics,
    RetrieverConfiguration,
)
from ragbench.cost.models import CostAccountingResult
from ragbench.regression.cli import main as regression_cli_main
from ragbench.regression.engine import evaluate_regression
from ragbench.regression.models import QualityThresholds, RegressionPolicy


def _make_eval_result(
    experiment_id: str,
    dataset_version: str = "1.1.0",
    dataset_fp: str = "fp_abc123",
    metrics: dict[str, float] | None = None,
    gen_metrics: dict[str, float] | None = None,
    cost_per_query: float | None = None,
    failure_rate: float = 0.0,
) -> EvaluationResult:
    m = metrics or {
        "recall_at_1": 0.8,
        "recall_at_3": 0.9,
        "recall_at_5": 1.0,
        "mrr": 0.85,
    }
    gm = gen_metrics or {
        "correctness": 0.80,
        "faithfulness": 1.0,
        "context_relevance": 0.75,
    }
    cost_acc = (
        CostAccountingResult(
            cost_status="available",
            total_cost=cost_per_query * 10 if cost_per_query else None,
            cost_per_query=cost_per_query,
        )
        if cost_per_query is not None
        else None
    )
    rel = ReliabilityMetrics(
        total_requests=10,
        successful_requests=int(10 * (1 - failure_rate)),
        failed_requests=int(10 * failure_rate),
        failure_rate=failure_rate,
    )
    return EvaluationResult(
        schema_version="5",
        experiment_id=experiment_id,
        timestamp=datetime.now(UTC),
        dataset_name="test_dataset",
        dataset_version=dataset_version,
        dataset_fingerprint=dataset_fp,
        corpus_documents={"doc_1": "doc_1"},
        retriever_configuration=RetrieverConfiguration(
            chunk_size=800,
            chunk_overlap=100,
            embedding_batch_size=32,
            qdrant_mode="memory",
        ),
        embedding_model="test-embedder",
        software_versions={"ragbench": "0.1.0"},
        top_k=5,
        query_count=10,
        metrics=m,
        queries=[],
        failures=[],
        generation_evaluation=GenerationEvaluationStatus(
            status="evaluated",
            aggregate_metrics=gm,
        ),
        cost_accounting=cost_acc,
        reliability=rel,
    )


def test_regression_decision_pass() -> None:
    baseline = _make_eval_result("base")
    candidate = _make_eval_result("cand")  # Equal metrics

    decision = evaluate_regression(baseline, candidate)
    assert decision.status == "pass"
    assert all(c.status == "pass" for c in decision.checks)


def test_regression_decision_fail_on_quality_drop() -> None:
    b_m = {"recall_at_1": 0.9, "recall_at_3": 0.9, "recall_at_5": 1.0, "mrr": 0.95}
    baseline = _make_eval_result("base", metrics=b_m)
    # Drop MRR by 0.10 (threshold is -0.02)
    c_m = {"recall_at_1": 0.9, "recall_at_3": 0.9, "recall_at_5": 1.0, "mrr": 0.85}
    candidate = _make_eval_result("cand", metrics=c_m)

    decision = evaluate_regression(baseline, candidate)
    assert decision.status == "fail"
    failed_checks = [c for c in decision.checks if c.status == "fail"]
    assert len(failed_checks) >= 1
    assert any(c.metric == "mrr" for c in failed_checks)


def test_regression_decision_inconclusive_on_dataset_mismatch() -> None:
    baseline = _make_eval_result("base", dataset_version="1.0.0")
    candidate = _make_eval_result("cand", dataset_version="1.1.0")

    decision = evaluate_regression(baseline, candidate)
    assert decision.status == "inconclusive"
    assert len(decision.warnings) > 0


def test_regression_decision_threshold_boundary() -> None:
    b_m = {"recall_at_1": 0.8, "recall_at_3": 0.8, "recall_at_5": 0.9, "mrr": 0.85}
    baseline = _make_eval_result("base", metrics=b_m)
    # Delta is exactly -0.02, threshold is -0.02 -> should pass
    c_m = {"recall_at_1": 0.8, "recall_at_3": 0.8, "recall_at_5": 0.9, "mrr": 0.83}
    candidate = _make_eval_result("cand", metrics=c_m)

    policy = RegressionPolicy(quality=QualityThresholds(mrr_min_delta=-0.02))
    decision = evaluate_regression(baseline, candidate, policy)
    mrr_check = next(c for c in decision.checks if c.metric == "mrr")
    assert mrr_check.status == "pass"


def test_regression_decision_missing_metric_inconclusive() -> None:
    baseline = _make_eval_result("base", metrics={"recall_at_1": 0.8, "mrr": 0.85})
    candidate = _make_eval_result(
        "cand",
        metrics={"recall_at_1": 0.8, "recall_at_3": 0.8, "mrr": 0.85},
    )

    decision = evaluate_regression(baseline, candidate)
    assert decision.status == "inconclusive"
    inc_checks = [c for c in decision.checks if c.status == "inconclusive"]
    assert any(c.metric in ("recall_at_3", "recall_at_5") for c in inc_checks)


def test_regression_cli_exit_codes(tmp_path) -> None:
    base = _make_eval_result("base")
    cand_pass = _make_eval_result("cand_pass")
    low_m = {"recall_at_1": 0.1, "recall_at_3": 0.1, "recall_at_5": 0.1, "mrr": 0.1}
    cand_fail = _make_eval_result("cand_fail", metrics=low_m)

    b_path = tmp_path / "base.json"
    p_path = tmp_path / "pass.json"
    f_path = tmp_path / "fail.json"

    b_path.write_text(base.model_dump_json(), encoding="utf-8")
    p_path.write_text(cand_pass.model_dump_json(), encoding="utf-8")
    f_path.write_text(cand_fail.model_dump_json(), encoding="utf-8")

    assert regression_cli_main(["--baseline", str(b_path), "--candidate", str(p_path)]) == 0
    assert regression_cli_main(["--baseline", str(b_path), "--candidate", str(f_path)]) == 1
