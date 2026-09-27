from pathlib import Path

import pytest

from ragbench.app.domain.errors import (
    DocumentDecodeError,
    EmptyDocumentError,
    UnsupportedDocumentTypeError,
)
from ragbench.app.ingestion.loader import DocumentLoader


def test_loads_text_with_stable_id_and_metadata(tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    path.write_text("alpha evidence", encoding="utf-8")

    document = DocumentLoader().load_path(path)

    assert document.text == "alpha evidence"
    assert document.metadata["filename"] == "notes.txt"
    assert document.metadata["source"] == str(path)
    assert document.metadata["document_id"] == document.id
    assert len(document.id) == 64


def test_loads_markdown_upload() -> None:
    document = DocumentLoader().load_bytes("notes.md", b"# Heading", source="upload")
    assert document.text == "# Heading"
    assert document.metadata["source"] == "upload"


@pytest.mark.parametrize("filename", ["notes.pdf", "notes", "notes.json"])
def test_rejects_unsupported_document_type(filename: str) -> None:
    with pytest.raises(UnsupportedDocumentTypeError):
        DocumentLoader().load_bytes(filename, b"content")


def test_rejects_empty_document() -> None:
    with pytest.raises(EmptyDocumentError):
        DocumentLoader().load_bytes("empty.txt", b"  \n")


def test_rejects_non_utf8_document() -> None:
    with pytest.raises(DocumentDecodeError):
        DocumentLoader().load_bytes("invalid.txt", b"\xff\xfe")
