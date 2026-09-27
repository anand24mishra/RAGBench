from datetime import UTC, datetime

import pytest

from benchmarks.timing import ExperimentTimingResult, LatencyStats
from evaluation.comparison import ComparisonError, compare_results, find_ranking_changes
from evaluation.models import (
    EvaluationResult,
    GenerationEvaluationStatus,
    QueryEvaluationResult,
    RetrievedDocumentResult,
    RetrieverConfiguration,
)


def make_eval_result(
    experiment_id: str,
    metrics: dict[str, float],
    *,
    dataset_version: str = "1.0.0",
    queries: list[QueryEvaluationResult] | None = None,
    timing: ExperimentTimingResult | None = None,
) -> EvaluationResult:
    if queries is None:
        queries = [
            QueryEvaluationResult(
                query_id="q001",
                question="q",
                relevant_documents=["doc_a"],
                retrieved=[
                    RetrievedDocumentResult(
                        rank=1,
                        document_id="doc_a",
                        raw_document_id="raw_a",
                        chunk_id="c_a",
                        score=0.9,
                    )
                ],
                retrieved_documents=["doc_a"],
                recall_at_1=metrics.get("recall_at_1", 1.0),
                recall_at_3=metrics.get("recall_at_3", 1.0),
                recall_at_5=metrics.get("recall_at_5", 1.0),
                reciprocal_rank=metrics.get("mrr", 1.0),
            )
        ]

    return EvaluationResult(
        experiment_id=experiment_id,
        timestamp=datetime.now(UTC),
        dataset_name="test-ds",
        dataset_version=dataset_version,
        dataset_fingerprint="fp123",
        corpus_documents={"doc_a": "raw_a"},
        retriever_configuration=RetrieverConfiguration(
            chunk_size=800,
            chunk_overlap=100,
            embedding_batch_size=32,
            qdrant_mode="memory",
        ),
        embedding_model="test-embedder",
        software_versions={"ragbench": "test"},
        top_k=5,
        query_count=len(queries),
        metrics=metrics,
        queries=queries,
        failures=[],
        generation_evaluation=GenerationEvaluationStatus(),
        timing=timing,
    )


def test_positive_delta() -> None:
    base = make_eval_result(
        "base", {"recall_at_1": 0.8, "recall_at_3": 0.8, "recall_at_5": 0.9, "mrr": 0.8}
    )
    exp = make_eval_result(
        "exp", {"recall_at_1": 0.9, "recall_at_3": 0.9, "recall_at_5": 1.0, "mrr": 0.9}
    )
    comp = compare_results(base, exp)

    assert comp.metrics["recall_at_1"].delta == pytest.approx(0.1)
    assert comp.metrics["recall_at_5"].delta == pytest.approx(0.1)
    assert comp.metrics["mrr"].delta == pytest.approx(0.1)


def test_negative_delta() -> None:
    base = make_eval_result(
        "base", {"recall_at_1": 0.9, "recall_at_3": 0.9, "recall_at_5": 1.0, "mrr": 0.9}
    )
    exp = make_eval_result(
        "exp", {"recall_at_1": 0.7, "recall_at_3": 0.8, "recall_at_5": 0.9, "mrr": 0.75}
    )
    comp = compare_results(base, exp)

    assert comp.metrics["recall_at_1"].delta == pytest.approx(-0.2)
    assert comp.metrics["recall_at_5"].delta == pytest.approx(-0.1)
    assert comp.metrics["mrr"].delta == pytest.approx(-0.15)


def test_zero_delta() -> None:
    base = make_eval_result(
        "base", {"recall_at_1": 0.9, "recall_at_3": 0.9, "recall_at_5": 1.0, "mrr": 0.925}
    )
    exp = make_eval_result(
        "exp", {"recall_at_1": 0.9, "recall_at_3": 0.9, "recall_at_5": 1.0, "mrr": 0.925}
    )
    comp = compare_results(base, exp)

    for name in ["recall_at_1", "recall_at_3", "recall_at_5", "mrr"]:
        assert comp.metrics[name].delta == pytest.approx(0.0)


def test_missing_metric_raises_comparison_error() -> None:
    base = make_eval_result("base", {"recall_at_1": 0.9, "recall_at_5": 1.0})
    exp = make_eval_result("exp", {"recall_at_1": 0.9, "recall_at_3": 0.9, "recall_at_5": 1.0})

    with pytest.raises(ComparisonError, match="different metric sets"):
        compare_results(base, exp)


def test_incompatible_dataset_versions() -> None:
    base = make_eval_result("base", {"recall_at_1": 0.9}, dataset_version="1.0.0")
    exp = make_eval_result("exp", {"recall_at_1": 0.9}, dataset_version="2.0.0")

    with pytest.raises(ComparisonError, match="different dataset versions"):
        compare_results(base, exp)


def test_ranking_changes_detected() -> None:
    base_q = QueryEvaluationResult(
        query_id="q007",
        question="What does the pipeline do?",
        relevant_documents=["doc_gen"],
        retrieved=[
            RetrievedDocumentResult(
                rank=1, document_id="doc_chunk", raw_document_id="r1", chunk_id="c1", score=0.8
            ),
            RetrievedDocumentResult(
                rank=2, document_id="doc_ret", raw_document_id="r2", chunk_id="c2", score=0.6
            ),
            RetrievedDocumentResult(
                rank=3, document_id="doc_obs", raw_document_id="r3", chunk_id="c3", score=0.4
            ),
            RetrievedDocumentResult(
                rank=4, document_id="doc_gen", raw_document_id="r4", chunk_id="c4", score=0.3
            ),
        ],
        retrieved_documents=["doc_chunk", "doc_ret", "doc_obs", "doc_gen"],
        recall_at_1=0.0,
        recall_at_3=0.0,
        recall_at_5=1.0,
        reciprocal_rank=0.25,
    )
    exp_q = QueryEvaluationResult(
        query_id="q007",
        question="What does the pipeline do?",
        relevant_documents=["doc_gen"],
        retrieved=[
            RetrievedDocumentResult(
                rank=1, document_id="doc_gen", raw_document_id="r4", chunk_id="c4", score=0.85
            ),
            RetrievedDocumentResult(
                rank=2, document_id="doc_chunk", raw_document_id="r1", chunk_id="c1", score=0.7
            ),
        ],
        retrieved_documents=["doc_gen", "doc_chunk"],
        recall_at_1=1.0,
        recall_at_3=1.0,
        recall_at_5=1.0,
        reciprocal_rank=1.0,
    )

    base = make_eval_result("base", {"recall_at_1": 0.0}, queries=[base_q])
    exp = make_eval_result("exp", {"recall_at_1": 1.0}, queries=[exp_q])

    changes = find_ranking_changes(base, exp)
    assert len(changes) == 1
    assert changes[0].query_id == "q007"
    assert changes[0].expected_document == "doc_gen"
    assert changes[0].baseline_rank == 4
    assert changes[0].experiment_rank == 1
    assert changes[0].baseline_score == pytest.approx(0.3)
    assert changes[0].experiment_score == pytest.approx(0.85)


def test_latency_metrics_compared() -> None:
    stats_base = LatencyStats(
        sample_size=1, mean_ms=10.0, p50_ms=10.0, p95_ms=10.0, p99_ms=10.0, min_ms=10.0, max_ms=10.0
    )
    stats_exp = LatencyStats(
        sample_size=1, mean_ms=5.0, p50_ms=5.0, p95_ms=5.0, p99_ms=5.0, min_ms=5.0, max_ms=5.0
    )

    timing_base = ExperimentTimingResult(
        sample_size=1,
        embedding_latency=stats_base,
        retrieval_latency=stats_base,
        total_runtime_ms=100.0,
        query_latencies=[],
    )
    timing_exp = ExperimentTimingResult(
        sample_size=1,
        embedding_latency=stats_exp,
        retrieval_latency=stats_exp,
        total_runtime_ms=60.0,
        query_latencies=[],
    )

    base = make_eval_result("base", {"recall_at_1": 1.0}, timing=timing_base)
    exp = make_eval_result("exp", {"recall_at_1": 1.0}, timing=timing_exp)

    comp = compare_results(base, exp)
    assert "mean_embedding_ms" in comp.latency_metrics
    assert comp.latency_metrics["mean_embedding_ms"].delta == -5.0
    assert comp.latency_metrics["total_runtime_ms"].delta == -40.0
