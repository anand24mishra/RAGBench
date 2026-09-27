from __future__ import annotations

import httpx
import pytest

from ragbench.app.domain.errors import LLMTimeoutError
from ragbench.app.generation.provider import OpenAICompatibleProvider
from ragbench.app.generation.retry import RetryPolicy, execute_with_retry


@pytest.mark.asyncio
async def test_retry_on_transient_failure_then_success() -> None:
    attempts = 0

    async def flaky_call() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            req = httpx.Request("POST", "http://example.com")
            res = httpx.Response(503, request=req)
            raise httpx.HTTPStatusError("503 Service Unavailable", request=req, response=res)
        return "success"

    policy = RetryPolicy(max_attempts=3, initial_backoff_seconds=0.01)
    result = await execute_with_retry(flaky_call, policy)
    assert result == "success"
    assert attempts == 3


@pytest.mark.asyncio
async def test_non_retryable_failure_fails_immediately() -> None:
    attempts = 0

    async def client_error_call() -> str:
        nonlocal attempts
        attempts += 1
        req = httpx.Request("POST", "http://example.com")
        res = httpx.Response(400, request=req)
        raise httpx.HTTPStatusError("400 Bad Request", request=req, response=res)

    policy = RetryPolicy(max_attempts=3, initial_backoff_seconds=0.01)
    with pytest.raises(httpx.HTTPStatusError):
        await execute_with_retry(client_error_call, policy)
    # Must NOT retry 400 Bad Request
    assert attempts == 1


@pytest.mark.asyncio
async def test_retry_exhaustion_raises() -> None:
    attempts = 0

    async def persistent_server_error() -> str:
        nonlocal attempts
        attempts += 1
        req = httpx.Request("POST", "http://example.com")
        res = httpx.Response(500, request=req)
        raise httpx.HTTPStatusError("500 Server Error", request=req, response=res)

    policy = RetryPolicy(max_attempts=2, initial_backoff_seconds=0.01)
    with pytest.raises(httpx.HTTPStatusError):
        await execute_with_retry(persistent_server_error, policy)
    assert attempts == 2


@pytest.mark.asyncio
async def test_timeout_retry_and_mapping() -> None:
    attempts = 0

    def mock_transport_timeout(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ReadTimeout("Read timed out")

    client = httpx.AsyncClient(transport=httpx.MockTransport(mock_transport_timeout))
    policy = RetryPolicy(max_attempts=2, initial_backoff_seconds=0.01)
    provider = OpenAICompatibleProvider(
        api_key="test-key",
        model="gpt-4o-mini",
        base_url="https://api.openai.com/v1",
        timeout_seconds=0.1,
        temperature=0.0,
        max_tokens=100,
        client=client,
        retry_policy=policy,
    )

    with pytest.raises(LLMTimeoutError):
        await provider.generate("hello", system_prompt="test")

    assert attempts == 2
