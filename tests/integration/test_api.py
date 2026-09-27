from fastapi.testclient import TestClient

from ragbench.app.context.builder import ContextBuilder
from ragbench.app.core.config import Settings
from ragbench.app.ingestion.chunker import FixedSizeChunker
from ragbench.app.ingestion.loader import DocumentLoader
from ragbench.app.ingestion.service import IngestionService
from ragbench.app.main import create_app
from ragbench.app.pipeline.rag import RAGPipeline
from ragbench.app.retrieval.retriever import SemanticRetriever
from ragbench.app.services import AppServices
from tests.fakes import DeterministicEmbedder, FakeLLMProvider, MemoryVectorStore


def make_client() -> tuple[TestClient, FakeLLMProvider]:
    settings = Settings(
        chunk_size=100,
        chunk_overlap=10,
        max_upload_bytes=1_000,
        llm_api_key="unused-in-test",
    )
    embedder = DeterministicEmbedder()
    store = MemoryVectorStore()
    llm = FakeLLMProvider("API answer")
    services = AppServices(
        ingestion=IngestionService(
            DocumentLoader(),
            FixedSizeChunker(settings.chunk_size, settings.chunk_overlap),
            embedder,
            store,
        ),
        pipeline=RAGPipeline(
            SemanticRetriever(embedder, store, settings.top_k),
            ContextBuilder(settings.context_char_limit),
            llm,
        ),
        vector_store=store,
        llm_provider=llm,
    )
    return TestClient(create_app(settings=settings, services=services)), llm


def test_health_ingest_and_query() -> None:
    client, llm = make_client()
    with client:
        health = client.get("/health")
        indexed = client.post(
            "/ingest",
            files={"file": ("alpha.md", b"# Alpha\nalpha evidence", "text/markdown")},
        )
        result = client.post("/query", json={"query": "alpha", "top_k": 1})

    assert health.json() == {"status": "ok"}
    assert indexed.status_code == 201
    assert indexed.json()["chunk_count"] == 1
    assert result.status_code == 200
    assert result.json()["answer"] == "API answer"
    assert result.json()["sources"][0]["metadata"]["filename"] == "alpha.md"
    assert result.json()["latency"]["embedding_ms"] >= 0
    assert result.headers["X-Request-ID"]
    assert len(llm.calls) == 1


def test_malformed_query_returns_explicit_error() -> None:
    client, _ = make_client()
    with client:
        response = client.post("/query", json={"query": "   "})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "request_validation_error"
    assert response.json()["detail"]["request_id"]


def test_invalid_document_returns_explicit_error() -> None:
    client, _ = make_client()
    with client:
        response = client.post(
            "/ingest",
            files={"file": ("document.pdf", b"not a PDF", "application/pdf")},
        )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "unsupported_document_type"
