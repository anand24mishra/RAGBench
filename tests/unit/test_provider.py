import httpx
import pytest

from ragbench.app.domain.errors import LLMProviderError, LLMTimeoutError
from ragbench.app.generation.provider import OpenAICompatibleProvider


def make_provider(handler: httpx.MockTransport) -> OpenAICompatibleProvider:
    client = httpx.AsyncClient(base_url="https://llm.example/v1", transport=handler)
    return OpenAICompatibleProvider(
        api_key="test-key",
        model="test-model",
        base_url="https://llm.example/v1",
        timeout_seconds=1,
        temperature=0,
        max_tokens=20,
        client=client,
    )


@pytest.mark.asyncio
async def test_provider_parses_answer_and_usage() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer test-key"
        return httpx.Response(
            200,
            json={
                "model": "returned-model",
                "choices": [{"message": {"content": "grounded answer"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 3},
            },
        )

    provider = make_provider(httpx.MockTransport(handler))
    result = await provider.generate("question", system_prompt="instructions")
    await provider._client.aclose()
    assert result.text == "grounded answer"
    assert result.model == "returned-model"
    assert result.input_tokens == 10
    assert result.output_tokens == 3


@pytest.mark.asyncio
async def test_provider_rejects_malformed_response() -> None:
    provider = make_provider(httpx.MockTransport(lambda _: httpx.Response(200, json={})))
    with pytest.raises(LLMProviderError, match="invalid response"):
        await provider.generate("question", system_prompt="instructions")
    await provider._client.aclose()


@pytest.mark.asyncio
async def test_provider_classifies_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    provider = make_provider(httpx.MockTransport(handler))
    with pytest.raises(LLMTimeoutError, match="timed out"):
        await provider.generate("question", system_prompt="instructions")
    await provider._client.aclose()
