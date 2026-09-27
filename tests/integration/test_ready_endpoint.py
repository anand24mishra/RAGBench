from __future__ import annotations

from fastapi.testclient import TestClient

from ragbench.app.main import create_app
from tests.integration.test_api import make_client


def test_health_liveness_endpoint() -> None:
    client, _ = make_client()
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_ready_readiness_endpoint_success() -> None:
    client, _ = make_client()
    res = client.get("/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["checks"]["services"] == "initialized"
    assert data["checks"]["pipeline"] == "ready"


def test_ready_readiness_endpoint_uninitialized() -> None:
    # App created without services explicitly set
    app = create_app()
    # Force state.services to None to test uninitialized state
    app.state.services = None
    client = TestClient(app)
    res = client.get("/ready")
    assert res.status_code == 503
    data = res.json()
    assert data["status"] == "not_ready"
    assert data["checks"]["services"] == "uninitialized"
