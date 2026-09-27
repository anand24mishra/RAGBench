import pytest
from fastapi.testclient import TestClient

from ragbench.app.core.config import Settings
from ragbench.app.embeddings.embedder import FastEmbedEmbedder
from ragbench.app.main import create_app
from ragbench.app.services import build_services


@pytest.mark.asyncio
async def test_fastembed_build_services_and_end_to_end_pipeline() -> None:
    settings = Settings(
        qdrant_url="memory",
        qdrant_collection="test_fastembed_coll",
        embedding_provider="fastembed",
        embedding_model="BAAI/bge-small-en-v1.5",
        llm_provider="mock",
    )
    services = await build_services(settings)
    try:
        assert isinstance(services.ingestion.embedder, FastEmbedEmbedder)
        assert services.ingestion.embedder.dimension == 384

        app = create_app(settings=settings, services=services)
        with TestClient(app) as client:
            # 1. Health check
            res_health = client.get("/health")
            assert res_health.status_code == 200
            assert res_health.json() == {"status": "ok"}

            # 2. Ready check
            res_ready = client.get("/ready")
            assert res_ready.status_code == 200
            assert res_ready.json()["status"] == "ready"

            # 3. Docs check
            res_docs = client.get("/docs")
            assert res_docs.status_code == 200

            # 4. Ingestion
            content = (
                b"# Architecture Overview\n"
                b"RAGBench uses FastEmbed in production for lightweight ONNX inference."
            )
            res_ingest = client.post(
                "/ingest",
                files={"file": ("architecture.md", content, "text/markdown")},
            )
            assert res_ingest.status_code == 201
            data = res_ingest.json()
            assert data["status"] == "indexed"
            assert data["document_id"]
            assert data["chunk_count"] >= 1

            # 5. Query
            res_query = client.post(
                "/query",
                json={"query": "What does RAGBench use in production?", "top_k": 2},
            )
            assert res_query.status_code == 200
            q_data = res_query.json()
            assert q_data["sources"]
            assert q_data["sources"][0]["metadata"]["filename"] == "architecture.md"
            assert q_data["latency"]["embedding_ms"] >= 0
            assert q_data["answer"]

            # 6. System config endpoint
            res_sys = client.get("/system/config")
            assert res_sys.status_code == 200
            sys_data = res_sys.json()
            assert sys_data["configuration"]["embedding_provider"] == "fastembed"
            assert sys_data["configuration"]["embedding_model"] == "BAAI/bge-small-en-v1.5"
    finally:
        await services.close()
