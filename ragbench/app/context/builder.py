from __future__ import annotations

from dataclasses import dataclass

from ragbench.app.domain.models import RetrievedChunk


@dataclass(frozen=True)
class ContextResult:
    text: str
    included_chunks: list[RetrievedChunk]


class ContextBuilder:
    def __init__(self, max_characters: int) -> None:
        if max_characters <= 0:
            raise ValueError("max_characters must be greater than zero")
        self.max_characters = max_characters

    def build(self, chunks: list[RetrievedChunk]) -> ContextResult:
        sections: list[str] = []
        included: list[RetrievedChunk] = []
        used = 0
        for rank, chunk in enumerate(chunks, start=1):
            filename = str(chunk.metadata.get("filename", "unknown"))
            section = (
                f"[Source {rank}]\n"
                f"filename: {filename}\n"
                f"document_id: {chunk.document_id}\n"
                f"chunk_id: {chunk.chunk_id}\n"
                f"content:\n{chunk.text}"
            )
            separator_length = 2 if sections else 0
            remaining = self.max_characters - used - separator_length
            if remaining <= 0:
                break
            if len(section) > remaining:
                if not sections:
                    sections.append(section[:remaining])
                    included.append(chunk)
                break
            sections.append(section)
            included.append(chunk)
            used += len(section) + separator_length
        return ContextResult(text="\n\n".join(sections), included_chunks=included)
