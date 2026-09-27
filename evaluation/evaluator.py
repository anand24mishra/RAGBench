from __future__ import annotations

from collections.abc import Sequence

from evaluation.dataset import EvaluationQuestion
from evaluation.models import (
    QueryEvaluationResult,
    RetrievalFailure,
    RetrievedDocumentResult,
)
from evaluation.retrieval_metrics import deduplicate_ranked_ids, recall_at_k, reciprocal_rank
from ragbench.app.retrieval.retriever import SemanticRetriever


class RetrievalEvaluator:
    def __init__(
        self,
        retriever: SemanticRetriever,
        raw_to_dataset_document_id: dict[str, str],
    ) -> None:
        self.retriever = retriever
        self.raw_to_dataset_document_id = raw_to_dataset_document_id

    async def evaluate(
        self,
        questions: Sequence[EvaluationQuestion],
        *,
        top_k: int,
    ) -> tuple[list[QueryEvaluationResult], list[RetrievalFailure]]:
        query_results: list[QueryEvaluationResult] = []
        failures: list[RetrievalFailure] = []

        for question in questions:
            retrieval = await self.retriever.retrieve(question.question, top_k)
            retrieved_details = [
                RetrievedDocumentResult(
                    rank=rank,
                    document_id=self.raw_to_dataset_document_id.get(
                        chunk.document_id, chunk.document_id
                    ),
                    raw_document_id=chunk.document_id,
                    chunk_id=chunk.chunk_id,
                    score=chunk.score,
                )
                for rank, chunk in enumerate(retrieval.chunks, start=1)
            ]
            retrieved_ids = [item.document_id for item in retrieved_details]
            unique_retrieved_ids = deduplicate_ranked_ids(retrieved_ids)
            relevant = set(question.relevant_documents)
            query_result = QueryEvaluationResult(
                query_id=question.id,
                question=question.question,
                relevant_documents=question.relevant_documents,
                retrieved=retrieved_details,
                retrieved_documents=unique_retrieved_ids,
                recall_at_1=recall_at_k(relevant, retrieved_ids, 1),
                recall_at_3=recall_at_k(relevant, retrieved_ids, 3),
                recall_at_5=recall_at_k(relevant, retrieved_ids, 5),
                reciprocal_rank=reciprocal_rank(relevant, retrieved_ids),
                embedding_ms=retrieval.embedding_ms,
                retrieval_ms=retrieval.search_ms,
                candidate_count=len(retrieval.chunks),
            )
            query_results.append(query_result)

            retrieved_at_k = set(unique_retrieved_ids[:top_k])
            for missing_document in sorted(relevant - retrieved_at_k):
                failures.append(
                    RetrievalFailure(
                        query_id=question.id,
                        expected_document=missing_document,
                        retrieved_documents=retrieved_ids,
                        retrieval_scores=[item.score for item in retrieved_details],
                    )
                )

        return query_results, failures


def aggregate_metrics(results: Sequence[QueryEvaluationResult]) -> dict[str, float]:
    if not results:
        raise ValueError("Cannot aggregate an empty evaluation result")
    count = len(results)
    return {
        "recall_at_1": sum(result.recall_at_1 for result in results) / count,
        "recall_at_3": sum(result.recall_at_3 for result in results) / count,
        "recall_at_5": sum(result.recall_at_5 for result in results) / count,
        "mrr": sum(result.reciprocal_rank for result in results) / count,
    }
