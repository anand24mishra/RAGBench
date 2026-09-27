from __future__ import annotations

import hashlib
from pathlib import Path

from ragbench.app.domain.errors import (
    DocumentDecodeError,
    EmptyDocumentError,
    UnsupportedDocumentTypeError,
)
from ragbench.app.domain.models import Document


class DocumentLoader:
    supported_suffixes = frozenset({".txt", ".md", ".markdown"})

    def load_path(self, path: Path) -> Document:
        if not path.is_file():
            raise UnsupportedDocumentTypeError(f"Document does not exist: {path.name}")
        return self.load_bytes(path.name, path.read_bytes(), source=str(path))

    def load_bytes(self, filename: str, content: bytes, *, source: str = "upload") -> Document:
        suffix = Path(filename).suffix.lower()
        if suffix not in self.supported_suffixes:
            supported = ", ".join(sorted(self.supported_suffixes))
            raise UnsupportedDocumentTypeError(
                f"Unsupported document type '{suffix or 'none'}'; supported types: {supported}"
            )
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DocumentDecodeError("Document must be valid UTF-8 text") from exc
        if not text.strip():
            raise EmptyDocumentError("Document contains no non-whitespace text")

        document_id = hashlib.sha256(content).hexdigest()
        return Document(
            id=document_id,
            text=text,
            metadata={
                "source": source,
                "filename": Path(filename).name,
                "document_id": document_id,
            },
        )
