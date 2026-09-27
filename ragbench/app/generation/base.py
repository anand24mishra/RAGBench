from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class GenerationResult:
    text: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, *, system_prompt: str) -> GenerationResult: ...

    async def close(self) -> None:
        return None
