import pytest
from pydantic import ValidationError

from ragbench.app.schemas.rag import QueryRequest


def test_query_is_trimmed() -> None:
    assert QueryRequest(query="  question  ").query == "question"


@pytest.mark.parametrize("query", ["", "  "])
def test_blank_query_is_rejected(query: str) -> None:
    with pytest.raises(ValidationError):
        QueryRequest(query=query)


def test_unknown_request_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        QueryRequest(query="question", unexpected=True)


@pytest.mark.parametrize("top_k", [0, 101])
def test_invalid_top_k_is_rejected(top_k: int) -> None:
    with pytest.raises(ValidationError):
        QueryRequest(query="question", top_k=top_k)
