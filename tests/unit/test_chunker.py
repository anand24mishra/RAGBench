import pytest

from ragbench.app.domain.models import Document
from ragbench.app.ingestion.chunker import FixedSizeChunker


def make_document(text: str) -> Document:
    return Document(
        id="document-1",
        text=text,
        metadata={"source": "test", "filename": "test.txt", "document_id": "document-1"},
    )


def test_short_document_produces_one_chunk() -> None:
    chunks = FixedSizeChunker(10, 2).chunk(make_document("short"))
    assert len(chunks) == 1
    assert chunks[0].text == "short"


def test_document_equal_to_chunk_size_produces_one_chunk() -> None:
    chunks = FixedSizeChunker(5, 1).chunk(make_document("12345"))
    assert [chunk.text for chunk in chunks] == ["12345"]


def test_long_document_is_split_deterministically() -> None:
    chunker = FixedSizeChunker(5, 0)
    first = chunker.chunk(make_document("abcdefghijk"))
    second = chunker.chunk(make_document("abcdefghijk"))
    assert [chunk.text for chunk in first] == ["abcde", "fghij", "k"]
    assert [chunk.chunk_id for chunk in first] == [chunk.chunk_id for chunk in second]


def test_overlap_is_preserved() -> None:
    chunks = FixedSizeChunker(5, 2).chunk(make_document("abcdefgh"))
    assert [chunk.text for chunk in chunks] == ["abcde", "defgh"]
    assert chunks[0].text[-2:] == chunks[1].text[:2]
    assert chunks[1].metadata["start_char"] == 3


def test_empty_input_produces_no_chunks() -> None:
    assert FixedSizeChunker(5, 1).chunk(make_document("")) == []


@pytest.mark.parametrize("size,overlap", [(0, 0), (5, -1), (5, 5), (5, 6)])
def test_invalid_configuration_is_rejected(size: int, overlap: int) -> None:
    with pytest.raises(ValueError):
        FixedSizeChunker(size, overlap)
