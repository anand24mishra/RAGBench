from __future__ import annotations

import json
import logging

from ragbench.app.core.logging import JsonFormatter, sanitize_log_value
from ragbench.observability.models import (
    GenerationObservation,
    RequestObservation,
    RetrievalObservation,
    TimingObservation,
)


def test_sanitize_log_value_redacts_sensitive_keys() -> None:
    assert sanitize_log_value("authorization", "Bearer my-secret-key") == "[REDACTED]"
    assert sanitize_log_value("api_key", "sk-1234567890") == "[REDACTED]"
    assert sanitize_log_value("password", "supersecret") == "[REDACTED]"
    assert sanitize_log_value("token", "jwt-token-string") == "[REDACTED]"


def test_sanitize_log_value_redacts_nested_structures() -> None:
    payload = {
        "headers": {
            "Authorization": "Bearer secret",
            "Content-Type": "application/json",
        },
        "query": "What is RAG?",
        "api_key": "secret-123",
    }
    sanitized = sanitize_log_value("request_payload", payload)
    assert sanitized["headers"]["Authorization"] == "[REDACTED]"
    assert sanitized["headers"]["Content-Type"] == "application/json"
    assert sanitized["query"] == "What is RAG?"
    assert sanitized["api_key"] == "[REDACTED]"


def test_json_formatter_sanitizes_record() -> None:
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="ragbench.test",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="test message",
        args=(),
        exc_info=None,
    )
    record.__dict__["authorization"] = "Bearer abcdef"
    record.__dict__["api_key"] = "sk-abcdef"
    record.__dict__["normal_field"] = "normal_value"

    formatted = formatter.format(record)
    data = json.loads(formatted)
    assert data["authorization"] == "[REDACTED]"
    assert data["api_key"] == "[REDACTED]"
    assert data["normal_field"] == "normal_value"


def test_request_observation_schema() -> None:
    obs = RequestObservation(
        request_id="req-123",
        experiment_id="exp-v5",
        query_id="q001",
        embedding_model="test-embedder",
        generation_model="test-llm",
        retrieval=RetrievalObservation(
            document_ids=["doc_1"],
            chunk_ids=["chunk_1"],
            scores=[0.92],
            count=1,
            embedding_ms=5.0,
            search_ms=1.2,
        ),
        generation=GenerationObservation(
            model="test-llm",
            input_tokens=150,
            output_tokens=30,
            total_tokens=180,
            generation_ms=12.5,
        ),
        timing=TimingObservation(
            embedding_ms=5.0,
            retrieval_ms=1.2,
            generation_ms=12.5,
            total_ms=18.7,
        ),
        outcome="success",
    )
    assert obs.request_id == "req-123"
    assert obs.retrieval.count == 1
    assert obs.generation.total_tokens == 180
    assert obs.timing.total_ms == 18.7
