from __future__ import annotations

from collections.abc import Iterable, Sequence


def deduplicate_ranked_ids(retrieved_ids: Iterable[str]) -> list[str]:
    """Remove duplicate document IDs while retaining first-occurrence rank."""
    seen: set[str] = set()
    result: list[str] = []
    for document_id in retrieved_ids:
        if document_id not in seen:
            seen.add(document_id)
            result.append(document_id)
    return result


def recall_at_k(relevant_ids: set[str], retrieved_ids: Sequence[str], k: int) -> float:
    if k <= 0:
        raise ValueError("k must be greater than zero")
    if not relevant_ids:
        raise ValueError("relevant_ids must not be empty")
    ranked_unique = deduplicate_ranked_ids(retrieved_ids)
    retrieved_relevant = relevant_ids.intersection(ranked_unique[:k])
    return len(retrieved_relevant) / len(relevant_ids)


def reciprocal_rank(relevant_ids: set[str], retrieved_ids: Sequence[str]) -> float:
    if not relevant_ids:
        raise ValueError("relevant_ids must not be empty")
    for rank, document_id in enumerate(deduplicate_ranked_ids(retrieved_ids), start=1):
        if document_id in relevant_ids:
            return 1.0 / rank
    return 0.0


def mean_reciprocal_rank(
    relevant_by_query: Sequence[set[str]],
    retrieved_by_query: Sequence[Sequence[str]],
) -> float:
    if len(relevant_by_query) != len(retrieved_by_query):
        raise ValueError("relevant and retrieved query counts must match")
    if not relevant_by_query:
        return 0.0
    return sum(
        reciprocal_rank(relevant, retrieved)
        for relevant, retrieved in zip(relevant_by_query, retrieved_by_query, strict=True)
    ) / len(relevant_by_query)
