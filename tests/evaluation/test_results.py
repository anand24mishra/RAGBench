from datetime import UTC, datetime
from pathlib import Path

import pytest

from evaluation.comparison import ComparisonError, compare_results, load_evaluation_result
from evaluation.models import (
    EvaluationResult,
    GenerationEvaluationStatus,
    QueryEvaluationResult,
    RetrieverConfiguration,
)
from evaluation.runner import write_result


def make_result(
    experiment_id: str,
    recall_at_1: float,
    *,
    dataset_version: str = "v1",
) -> EvaluationResult:
    query = QueryEvaluationResult(
        query_id="q001",
        question="question",
        relevant_documents=["doc-a"],
        retrieved=[],
        retrieved_documents=[],
        recall_at_1=recall_at_1,
        recall_at_3=1.0,
        recall_at_5=1.0,
        reciprocal_rank=recall_at_1,
    )
    return EvaluationResult(
        experiment_id=experiment_id,
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        dataset_name="fixture",
        dataset_version=dataset_version,
        dataset_fingerprint="fixture-fingerprint",
        corpus_documents={"doc-a": "raw-doc-a"},
        retriever_configuration=RetrieverConfiguration(
            chunk_size=800,
            chunk_overlap=100,
            embedding_batch_size=32,
            qdrant_mode="memory",
        ),
        embedding_model="fixture-model",
        software_versions={"ragbench": "test"},
        top_k=5,
        query_count=1,
        metrics={
            "recall_at_1": recall_at_1,
            "recall_at_3": 1.0,
            "recall_at_5": 1.0,
            "mrr": recall_at_1,
        },
        queries=[query],
        failures=[],
        generation_evaluation=GenerationEvaluationStatus(),
    )


def test_baseline_result_serialization_round_trip(tmp_path: Path) -> None:
    result_path = tmp_path / "baseline.json"
    summary_path = tmp_path / "baseline.md"
    baseline = make_result("baseline", 0.5)

    write_result(baseline, result_path, summary_path)
    loaded = load_evaluation_result(result_path)

    assert loaded == baseline
    assert loaded.generation_evaluation.status == "not_implemented"
    assert "Recall@1" in summary_path.read_text(encoding="utf-8")


def test_experiment_comparison_calculates_signed_deltas() -> None:
    comparison = compare_results(make_result("baseline", 0.5), make_result("candidate", 0.75))
    metric = comparison.metrics["recall_at_1"]
    assert metric.baseline == 0.5
    assert metric.experiment == 0.75
    assert metric.delta == 0.25
    assert comparison.metrics["mrr"].delta == 0.25


def test_comparison_rejects_different_dataset_versions() -> None:
    with pytest.raises(ComparisonError, match="different dataset versions"):
        compare_results(
            make_result("baseline", 0.5, dataset_version="v1"),
            make_result("candidate", 0.5, dataset_version="v2"),
        )


def test_comparison_rejects_changed_dataset_content() -> None:
    baseline = make_result("baseline", 0.5)
    candidate = make_result("candidate", 0.5).model_copy(update={"dataset_fingerprint": "changed"})
    with pytest.raises(ComparisonError, match="different dataset fingerprints"):
        compare_results(baseline, candidate)
