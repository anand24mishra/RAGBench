from ragbench.app.context.builder import ContextBuilder
from ragbench.app.domain.models import RetrievedChunk


def chunk(identifier: str, text: str, score: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=identifier,
        document_id=f"doc-{identifier}",
        text=text,
        score=score,
        metadata={"filename": f"{identifier}.txt"},
    )


def test_context_preserves_rank_and_source_boundaries() -> None:
    result = ContextBuilder(1_000).build(
        [chunk("first", "alpha", 0.9), chunk("second", "beta", 0.8)]
    )
    assert result.text.index("[Source 1]") < result.text.index("[Source 2]")
    assert "filename: first.txt" in result.text
    assert "chunk_id: second" in result.text
    assert [item.chunk_id for item in result.included_chunks] == ["first", "second"]


def test_context_limit_excludes_later_chunks() -> None:
    first = chunk("first", "alpha", 0.9)
    second = chunk("second", "beta", 0.8)
    first_only_length = len(ContextBuilder(1_000).build([first]).text)
    result = ContextBuilder(first_only_length).build([first, second])
    assert [item.chunk_id for item in result.included_chunks] == ["first"]


def test_first_chunk_is_truncated_to_hard_limit() -> None:
    result = ContextBuilder(40).build([chunk("first", "x" * 100, 0.9)])
    assert len(result.text) == 40
    assert len(result.included_chunks) == 1


def test_empty_results_produce_empty_context() -> None:
    result = ContextBuilder(100).build([])
    assert result.text == ""
    assert result.included_chunks == []
