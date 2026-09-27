import numpy as np
import pytest

from ragbench.app.domain.errors import EmbeddingError
from ragbench.app.embeddings.embedder import SentenceTransformerEmbedder


class StubSentenceTransformer:
    def get_sentence_embedding_dimension(self) -> int:
        return 3

    def encode(self, texts: list[str], **_: object) -> np.ndarray:
        return np.asarray([[float(len(text)), 1.0, 0.5] for text in texts])


def make_embedder() -> SentenceTransformerEmbedder:
    return SentenceTransformerEmbedder("stub", model=StubSentenceTransformer())


def test_document_embedding_shape() -> None:
    embedder = make_embedder()
    vectors = embedder.embed_documents(["one", "two words"])
    assert embedder.dimension == 3
    assert len(vectors) == 2
    assert all(len(vector) == 3 for vector in vectors)


def test_empty_document_batch_returns_empty_list() -> None:
    assert make_embedder().embed_documents([]) == []


def test_query_and_document_embeddings_are_compatible() -> None:
    embedder = make_embedder()
    assert embedder.embed_query("query") == embedder.embed_documents(["query"])[0]


@pytest.mark.parametrize("value", ["", "   "])
def test_empty_query_is_rejected(value: str) -> None:
    with pytest.raises(EmbeddingError):
        make_embedder().embed_query(value)
