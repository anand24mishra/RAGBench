from datetime import UTC, datetime
from pathlib import Path

import pytest
from qdrant_client import AsyncQdrantClient

from benchmarks.timing import ExperimentTimingResult, LatencyStats, QueryLatency
from evaluation.dataset import EvaluationQuestion
from evaluation.evaluator import RetrievalEvaluator, aggregate_metrics
from evaluation.models import (
    EvaluationResult,
    GenerationEvaluationStatus,
    QueryEvaluationResult,
    RetrievedDocumentResult,
    RetrieverConfiguration,
)
from evaluation.runner import REPOSITORY_ROOT, _corpus_files, _dataset_fingerprint, load_config
from ragbench.app.domain.errors import EmbeddingError
from ragbench.app.domain.models import Chunk
from ragbench.app.embeddings.embedder import SentenceTransformerEmbedder
from ragbench.app.retrieval.retriever import SemanticRetriever
from ragbench.app.vector_store.qdrant import QdrantVectorStore
from ragbench.experiments.config import ExperimentConfig
from tests.fakes import DeterministicEmbedder, MemoryVectorStore


def test_experiment_result_serialization_preserves_all_v3_fields() -> None:
    stats = LatencyStats(
        sample_size=10,
        mean_ms=12.4,
        p50_ms=11.2,
        p95_ms=18.5,
        p99_ms=21.0,
        min_ms=5.0,
        max_ms=22.0,
    )
    timing = ExperimentTimingResult(
        sample_size=10,
        embedding_latency=stats,
        retrieval_latency=stats,
        total_runtime_ms=150.0,
        query_latencies=[
            QueryLatency(query_id="q001", embedding_ms=12.0, retrieval_ms=1.5, total_ms=13.5)
        ],
    )
    query = QueryEvaluationResult(
        query_id="q001",
        question="What is this?",
        relevant_documents=["doc1"],
        retrieved=[
            RetrievedDocumentResult(
                rank=1, document_id="doc1", raw_document_id="raw1", chunk_id="c1", score=0.88
            )
        ],
        retrieved_documents=["doc1"],
        recall_at_1=1.0,
        recall_at_3=1.0,
        recall_at_5=1.0,
        reciprocal_rank=1.0,
        embedding_ms=12.0,
        retrieval_ms=1.5,
        candidate_count=1,
    )
    result = EvaluationResult(
        schema_version="3",
        experiment_id="test-exp-01",
        timestamp=datetime.now(UTC),
        dataset_name="test-ds",
        dataset_version="1.0.0",
        dataset_fingerprint="sha256-test",
        corpus_documents={"doc1": "raw1"},
        retriever_configuration=RetrieverConfiguration(
            chunk_size=400,
            chunk_overlap=50,
            embedding_batch_size=32,
            qdrant_mode="memory",
        ),
        embedding_model="test-embedder",
        embedding_dimension=384,
        software_versions={"ragbench": "test"},
        top_k=5,
        query_count=1,
        metrics={"recall_at_1": 1.0, "recall_at_3": 1.0, "recall_at_5": 1.0, "mrr": 1.0},
        queries=[query],
        failures=[],
        generation_evaluation=GenerationEvaluationStatus(),
        timing=timing,
        hypothesis="Testing preservation of all fields",
        changed_parameter="chunk_size=400, chunk_overlap=50",
        candidate_count=5,
        interpretation="Directional check on test workload",
        decision="Retain for further investigation",
    )

    serialized = result.model_dump_json()
    deserialized = EvaluationResult.model_validate_json(serialized)

    assert deserialized == result
    assert deserialized.embedding_dimension == 384
    assert deserialized.hypothesis == "Testing preservation of all fields"
    assert deserialized.changed_parameter == "chunk_size=400, chunk_overlap=50"
    assert deserialized.timing is not None
    assert deserialized.timing.total_runtime_ms == 150.0
    assert deserialized.timing.embedding_latency.mean_ms == 12.4
    assert deserialized.decision == "Retain for further investigation"


@pytest.mark.asyncio
async def test_experiments_use_independent_vector_stores_no_contamination() -> None:
    embedder = DeterministicEmbedder()
    client1 = AsyncQdrantClient(location=":memory:")
    client2 = AsyncQdrantClient(location=":memory:")

    store1 = QdrantVectorStore(None, "collection_exp_a", client=client1)
    store2 = QdrantVectorStore(None, "collection_exp_b", client=client2)

    try:
        chunks_a = [Chunk(chunk_id="ca1", document_id="doc_a", text="apple", metadata={})]
        chunks_b = [Chunk(chunk_id="cb1", document_id="doc_b", text="banana", metadata={})]

        await store1.ensure_collection(embedder.dimension)
        await store1.upsert(chunks_a, embedder.embed_documents(["apple"]))

        await store2.ensure_collection(embedder.dimension)
        await store2.upsert(chunks_b, embedder.embed_documents(["banana"]))

        # Store 1 should only see chunks_a
        results_1 = await store1.search(embedder.embed_query("apple"), top_k=5)
        assert len(results_1) == 1
        assert results_1[0].document_id == "doc_a"

        # Store 2 should only see chunks_b
        results_2 = await store2.search(embedder.embed_query("apple"), top_k=5)
        assert len(results_2) == 1
        assert results_2[0].document_id == "doc_b"
    finally:
        await store1.close()
        await store2.close()


@pytest.mark.asyncio
async def test_top_k_evaluation_semantics() -> None:
    embedder = DeterministicEmbedder()
    store = MemoryVectorStore()
    await store.ensure_collection(embedder.dimension)

    chunks = [
        Chunk(chunk_id="c1", document_id="doc1", text="first", metadata={}),
        Chunk(chunk_id="c2", document_id="doc2", text="second", metadata={}),
        Chunk(chunk_id="c3", document_id="doc3", text="third", metadata={}),
        Chunk(chunk_id="c4", document_id="doc4", text="fourth", metadata={}),
    ]
    await store.upsert(chunks, embedder.embed_documents([c.text for c in chunks]))

    mapping = {c.document_id: c.document_id for c in chunks}
    retriever_k1 = SemanticRetriever(embedder, store, default_top_k=1)
    evaluator_k1 = RetrievalEvaluator(retriever_k1, mapping)

    # Question targeting doc4, which is at rank 4
    question = EvaluationQuestion(
        id="q-deep",
        question="first",  # query closest to first
        relevant_documents=["doc4"],
    )

    results_k1, failures_k1 = await evaluator_k1.evaluate([question], top_k=1)
    # top_k=1 only returns doc1
    assert len(results_k1[0].retrieved) == 1
    assert results_k1[0].retrieved[0].document_id == "doc1"
    assert results_k1[0].recall_at_1 == 0.0
    assert results_k1[0].recall_at_3 == 0.0
    assert results_k1[0].recall_at_5 == 0.0
    assert results_k1[0].reciprocal_rank == 0.0
    assert len(failures_k1) == 1

    # At top_k=5, doc4 is returned at rank 4
    retriever_k5 = SemanticRetriever(embedder, store, default_top_k=5)
    evaluator_k5 = RetrievalEvaluator(retriever_k5, mapping)
    results_k5, failures_k5 = await evaluator_k5.evaluate([question], top_k=5)

    assert len(results_k5[0].retrieved) == 4
    assert results_k5[0].recall_at_1 == 0.0
    assert results_k5[0].recall_at_3 == 0.0
    assert results_k5[0].recall_at_5 == 1.0
    assert results_k5[0].reciprocal_rank == 0.25
    assert len(failures_k5) == 0


def test_dataset_fingerprint_is_preserved() -> None:
    baseline_path = REPOSITORY_ROOT / "experiments" / "baseline" / "config.yaml"
    cfg = load_config(baseline_path)
    corpus = _corpus_files(cfg.corpus_path)
    fingerprint1 = _dataset_fingerprint(cfg, corpus)
    fingerprint2 = _dataset_fingerprint(cfg, corpus)

    assert fingerprint1 == fingerprint2
    assert len(fingerprint1) == 64  # SHA-256 hex string


def test_embedding_failure_does_not_silently_fallback() -> None:
    with pytest.raises(EmbeddingError, match="Failed to load embedding model"):
        SentenceTransformerEmbedder("nonexistent-embedding-model-xyz-12345")


@pytest.mark.asyncio
async def test_same_configuration_and_same_dataset_produce_equivalent_evaluation_structure() -> (
    None
):
    embedder = DeterministicEmbedder()
    client1 = AsyncQdrantClient(location=":memory:")
    client2 = AsyncQdrantClient(location=":memory:")
    store1 = QdrantVectorStore(None, "col1", client=client1)
    store2 = QdrantVectorStore(None, "col2", client=client2)

    try:
        chunks = [
            Chunk(chunk_id="c1", document_id="doc1", text="some text", metadata={}),
            Chunk(chunk_id="c2", document_id="doc2", text="more text", metadata={}),
        ]
        await store1.ensure_collection(embedder.dimension)
        await store2.ensure_collection(embedder.dimension)
        await store1.upsert(chunks, embedder.embed_documents([c.text for c in chunks]))
        await store2.upsert(chunks, embedder.embed_documents([c.text for c in chunks]))

        mapping = {"doc1": "doc1", "doc2": "doc2"}
        eval1 = RetrievalEvaluator(SemanticRetriever(embedder, store1, default_top_k=2), mapping)
        eval2 = RetrievalEvaluator(SemanticRetriever(embedder, store2, default_top_k=2), mapping)

        q = EvaluationQuestion(id="q1", question="some text", relevant_documents=["doc1"])
        res1, fail1 = await eval1.evaluate([q], top_k=2)
        res2, fail2 = await eval2.evaluate([q], top_k=2)

        assert aggregate_metrics(res1) == aggregate_metrics(res2)
        assert res1[0].retrieved_documents == res2[0].retrieved_documents
        assert [r.score for r in res1[0].retrieved] == [r.score for r in res2[0].retrieved]
        assert len(fail1) == len(fail2)
    finally:
        await store1.close()
        await store2.close()


try:
    import sentence_transformers  # noqa: F401

    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False


@pytest.mark.skipif(
    not HAS_SENTENCE_TRANSFORMERS,
    reason="sentence-transformers required for historical experiments",
)
@pytest.mark.asyncio
async def test_chunking_experiment_execution(tmp_path: Path) -> None:
    from ragbench.experiments.config import load_experiment_config
    from ragbench.experiments.runner import run_experiment

    cfg = ExperimentConfig(
        experiment_id="test-chunking",
        dataset_version="1.0.0",
        chunk_size=400,
        chunk_overlap=50,
        top_k=5,
        result_path=tmp_path / "test_chunk.json",
        summary_path=tmp_path / "test_chunk.md",
    )
    baseline_path = REPOSITORY_ROOT / "experiments" / "baseline" / "config.yaml"
    baseline_cfg = load_experiment_config(baseline_path)

    result, comparison = await run_experiment(cfg, baseline_config=baseline_cfg, write_reports=True)

    assert result.experiment_id == "test-chunking"
    assert result.metrics["recall_at_5"] == 1.0
    assert (tmp_path / "test_chunk.json").exists()
    assert (tmp_path / "test_chunk.md").exists()
    assert comparison is not None
    assert "recall_at_5" in comparison.metrics
