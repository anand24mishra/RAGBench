from __future__ import annotations

from typing import Any

import httpx

from ragbench.app.domain.errors import ConfigurationError, LLMProviderError, LLMTimeoutError
from ragbench.app.generation.base import GenerationResult, LLMProvider
from ragbench.app.generation.retry import RetryPolicy, execute_with_retry


class OpenAICompatibleProvider(LLMProvider):
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str,
        timeout_seconds: float,
        temperature: float,
        max_tokens: int,
        client: httpx.AsyncClient | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        if not api_key:
            raise ConfigurationError("LLM_API_KEY is required for the openai provider")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds
        self.base_url = base_url.rstrip("/")
        self.retry_policy = retry_policy or RetryPolicy()
        self._authorization_header = {"Authorization": f"Bearer {api_key}"}
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout_seconds,
        )

    async def generate(self, prompt: str, *, system_prompt: str) -> GenerationResult:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        endpoint = (
            "/chat/completions"
            if str(self._client.base_url).strip("/")
            else f"{self.base_url}/chat/completions"
        )

        async def _call() -> httpx.Response:
            res = await self._client.post(
                endpoint,
                json=payload,
                headers=self._authorization_header,
            )
            res.raise_for_status()
            return res

        try:
            response = await execute_with_retry(
                _call,
                self.retry_policy,
                operation_name="llm_generate",
            )
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError("LLM request timed out") from exc
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            if code == 429:
                raise LLMProviderError("LLM provider rate limit exceeded (429)") from exc
            if 400 <= code < 500:
                raise LLMProviderError(f"LLM provider client error ({code})") from exc
            raise LLMProviderError(f"LLM provider server error ({code})") from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError("LLM provider request failed") from exc

        try:
            body: dict[str, Any] = response.json()
            text = body["choices"][0]["message"]["content"]
            if not isinstance(text, str) or not text.strip():
                raise ValueError("empty model response")
            usage = body.get("usage") or {}
            input_tokens = usage.get("prompt_tokens")
            output_tokens = usage.get("completion_tokens")
            response_model = str(body.get("model") or self.model)
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise LLMProviderError("LLM provider returned an invalid response") from exc

        return GenerationResult(
            text=text,
            model=response_model,
            input_tokens=int(input_tokens) if input_tokens is not None else None,
            output_tokens=int(output_tokens) if output_tokens is not None else None,
        )

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()
