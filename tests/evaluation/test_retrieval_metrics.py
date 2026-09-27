import pytest

from evaluation.retrieval_metrics import (
    deduplicate_ranked_ids,
    mean_reciprocal_rank,
    recall_at_k,
    reciprocal_rank,
)


def test_recall_at_k_with_multiple_relevant_documents() -> None:
    relevant = {"a", "b"}
    retrieved = ["a", "x", "b", "y"]
    assert recall_at_k(relevant, retrieved, 1) == 0.5
    assert recall_at_k(relevant, retrieved, 3) == 1.0
    assert recall_at_k(relevant, retrieved, 5) == 1.0


def test_empty_retrieval_scores_zero() -> None:
    assert recall_at_k({"a"}, [], 5) == 0.0
    assert reciprocal_rank({"a"}, []) == 0.0


def test_duplicate_retrieved_ids_are_collapsed_before_rank_cutoff() -> None:
    retrieved = ["x", "x", "a", "a"]
    assert deduplicate_ranked_ids(retrieved) == ["x", "a"]
    assert recall_at_k({"a"}, retrieved, 2) == 1.0
    assert reciprocal_rank({"a"}, retrieved) == 0.5


def test_relevant_document_outside_top_k() -> None:
    retrieved = ["x", "y", "a"]
    assert recall_at_k({"a"}, retrieved, 2) == 0.0
    assert recall_at_k({"a"}, retrieved, 3) == 1.0
    assert reciprocal_rank({"a"}, retrieved) == pytest.approx(1 / 3)


def test_mean_reciprocal_rank() -> None:
    value = mean_reciprocal_rank(
        [{"a"}, {"b"}, {"c"}],
        [["a"], ["x", "b"], []],
    )
    assert value == 0.5


@pytest.mark.parametrize("k", [0, -1])
def test_recall_rejects_invalid_k(k: int) -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        recall_at_k({"a"}, ["a"], k)
