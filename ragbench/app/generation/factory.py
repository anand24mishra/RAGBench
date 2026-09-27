from ragbench.app.core.config import Settings
from ragbench.app.domain.errors import ConfigurationError
from ragbench.app.generation.base import LLMProvider
from ragbench.app.generation.mock import MockLLMProvider
from ragbench.app.generation.provider import OpenAICompatibleProvider


def create_llm_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "mock":
        return MockLLMProvider()

    if settings.llm_provider != "openai":
        raise ConfigurationError(f"Unsupported LLM provider: {settings.llm_provider}")

    key = settings.llm_api_key.get_secret_value() if settings.llm_api_key else ""
    return OpenAICompatibleProvider(
        api_key=key,
        model=settings.llm_model,
        base_url=settings.llm_base_url,
        timeout_seconds=settings.llm_timeout_seconds,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
    )
