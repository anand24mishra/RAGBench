import pytest

from evaluation.dataset import EvaluationQuestion
from evaluation.evaluator import RetrievalEvaluator, aggregate_metrics
from ragbench.app.domain.models import Chunk
from ragbench.app.retrieval.retriever import SemanticRetriever
from tests.fakes import DeterministicEmbedder, MemoryVectorStore


@pytest.mark.asyncio
async def test_evaluator_uses_production_retriever_and_records_failure() -> None:
    embedder = DeterministicEmbedder()
    store = MemoryVectorStore()
    chunks = [
        Chunk(chunk_id="alpha", document_id="raw-alpha", text="alpha", metadata={}),
        Chunk(chunk_id="beta", document_id="raw-beta", text="beta", metadata={}),
    ]
    await store.ensure_collection(embedder.dimension)
    await store.upsert(chunks, embedder.embed_documents([chunk.text for chunk in chunks]))
    evaluator = RetrievalEvaluator(
        SemanticRetriever(embedder, store, default_top_k=1),
        {"raw-alpha": "alpha-doc", "raw-beta": "beta-doc"},
    )
    questions = [
        EvaluationQuestion(
            id="q-alpha",
            question="alpha",
            relevant_documents=["alpha-doc"],
        ),
        EvaluationQuestion(
            id="q-missing",
            question="alpha",
            relevant_documents=["beta-doc"],
        ),
    ]

    results, failures = await evaluator.evaluate(questions, top_k=1)
    metrics = aggregate_metrics(results)

    assert results[0].retrieved_documents == ["alpha-doc"]
    assert results[0].recall_at_1 == 1.0
    assert results[1].recall_at_1 == 0.0
    assert failures[0].query_id == "q-missing"
    assert failures[0].expected_document == "beta-doc"
    assert failures[0].retrieved_documents == ["alpha-doc"]
    assert len(failures[0].retrieval_scores) == 1
    assert metrics["recall_at_1"] == 0.5
    assert metrics["mrr"] == 0.5


@pytest.mark.asyncio
async def test_evaluator_handles_empty_retrieval() -> None:
    evaluator = RetrievalEvaluator(
        SemanticRetriever(DeterministicEmbedder(), MemoryVectorStore(), default_top_k=5),
        {},
    )
    question = EvaluationQuestion(
        id="q-empty",
        question="alpha",
        relevant_documents=["alpha-doc"],
    )

    results, failures = await evaluator.evaluate([question], top_k=5)

    assert results[0].retrieved == []
    assert results[0].recall_at_5 == 0.0
    assert results[0].reciprocal_rank == 0.0
    assert failures[0].retrieved_documents == []
    assert failures[0].retrieval_scores == []
