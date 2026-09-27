from __future__ import annotations

import hashlib

from ragbench.app.domain.models import Chunk, Document


class FixedSizeChunker:
    def __init__(self, chunk_size: int, chunk_overlap: int) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, document: Document) -> list[Chunk]:
        if not document.text:
            return []

        step = self.chunk_size - self.chunk_overlap
        chunks: list[Chunk] = []
        for index, start in enumerate(range(0, len(document.text), step)):
            end = min(start + self.chunk_size, len(document.text))
            text = document.text[start:end]
            if not text:
                break
            chunk_id = hashlib.sha256(f"{document.id}:{start}:{end}".encode()).hexdigest()
            metadata = {
                **document.metadata,
                "chunk_index": index,
                "start_char": start,
                "end_char": end,
            }
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_id=document.id,
                    text=text,
                    metadata=metadata,
                )
            )
            if end == len(document.text):
                break
        return chunks
