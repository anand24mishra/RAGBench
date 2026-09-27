import numpy as np
import pytest

from ragbench.app.core.config import Settings
from ragbench.app.domain.errors import ConfigurationError, EmbeddingError
from ragbench.app.embeddings.embedder import FastEmbedEmbedder, SentenceTransformerEmbedder
from ragbench.app.services import create_embedder


class StubSentenceTransformer:
    def get_sentence_embedding_dimension(self) -> int:
        return 3

    def encode(self, texts: list[str], **_: object) -> np.ndarray:
        return np.asarray([[float(len(text)), 1.0, 0.5] for text in texts])


class StubFastEmbedModel:
    def __init__(self, dimension: int = 3, fail: bool = False, bad_shape: bool = False) -> None:
        self.embedding_size = dimension
        self._fail = fail
        self._bad_shape = bad_shape

    def embed(self, texts: list[str], batch_size: int = 32) -> list[np.ndarray]:
        if self._fail:
            raise RuntimeError("FastEmbed internal failure")
        if self._bad_shape:
            # Yield fewer vectors than texts
            return [np.asarray([1.0, 2.0, 3.0])]
        return [np.asarray([float(len(text)), 1.0, 0.5]) for text in texts]


def make_st_embedder() -> SentenceTransformerEmbedder:
    return SentenceTransformerEmbedder("stub", model=StubSentenceTransformer())


def make_fastembed_embedder(
    dimension: int = 3, fail: bool = False, bad_shape: bool = False
) -> FastEmbedEmbedder:
    return FastEmbedEmbedder(
        "stub",
        model=StubFastEmbedModel(dimension=dimension, fail=fail, bad_shape=bad_shape),
    )


# --- SentenceTransformerEmbedder tests (historical baseline preserved) ---


def test_document_embedding_shape() -> None:
    embedder = make_st_embedder()
    vectors = embedder.embed_documents(["one", "two words"])
    assert embedder.dimension == 3
    assert len(vectors) == 2
    assert all(len(vector) == 3 for vector in vectors)


def test_empty_document_batch_returns_empty_list() -> None:
    assert make_st_embedder().embed_documents([]) == []


def test_query_and_document_embeddings_are_compatible() -> None:
    embedder = make_st_embedder()
    assert embedder.embed_query("query") == embedder.embed_documents(["query"])[0]


@pytest.mark.parametrize("value", ["", "   "])
def test_empty_query_is_rejected(value: str) -> None:
    with pytest.raises(EmbeddingError):
        make_st_embedder().embed_query(value)


# --- FastEmbedEmbedder tests (lightweight production embedder) ---


def test_fastembed_document_embedding_shape() -> None:
    embedder = make_fastembed_embedder()
    vectors = embedder.embed_documents(["one", "two words"])
    assert embedder.dimension == 3
    assert len(vectors) == 2
    assert all(isinstance(v, list) for v in vectors)
    assert all(len(vector) == 3 for vector in vectors)
    assert vectors[0] == [3.0, 1.0, 0.5]


def test_fastembed_empty_document_batch_returns_empty_list() -> None:
    assert make_fastembed_embedder().embed_documents([]) == []


def test_fastembed_query_and_document_embeddings_are_compatible() -> None:
    embedder = make_fastembed_embedder()
    assert embedder.embed_query("query") == embedder.embed_documents(["query"])[0]


@pytest.mark.parametrize("value", ["", "   "])
def test_fastembed_empty_query_is_rejected(value: str) -> None:
    with pytest.raises(EmbeddingError, match="must not be empty"):
        make_fastembed_embedder().embed_query(value)


@pytest.mark.parametrize("value", ["", "   "])
def test_fastembed_empty_document_in_batch_is_rejected(value: str) -> None:
    with pytest.raises(EmbeddingError, match="must not be empty"):
        make_fastembed_embedder().embed_documents(["valid", value])


def test_fastembed_batch_size_validation() -> None:
    with pytest.raises(ValueError, match="batch_size must be greater than zero"):
        FastEmbedEmbedder("stub", batch_size=0, model=StubFastEmbedModel())


def test_fastembed_missing_dimension_raises_error() -> None:
    class NoDimModel:
        def embed(self, texts: list[str], **kwargs: object) -> list[np.ndarray]:
            return [np.zeros(3) for _ in texts]

    with pytest.raises(EmbeddingError, match="did not report a vector dimension"):
        FastEmbedEmbedder("stub", model=NoDimModel())


def test_fastembed_internal_error_wrapped_in_embedding_error() -> None:
    embedder = make_fastembed_embedder(fail=True)
    with pytest.raises(EmbeddingError, match="Document embedding failed"):
        embedder.embed_documents(["test"])


def test_fastembed_unexpected_shape_raises_error() -> None:
    embedder = make_fastembed_embedder(bad_shape=True)
    with pytest.raises(EmbeddingError, match="unexpected output shape"):
        embedder.embed_documents(["one", "two"])


def test_fastembed_nonexistent_model_raises_error() -> None:
    with pytest.raises(EmbeddingError, match="Failed to load embedding model"):
        FastEmbedEmbedder("nonexistent-model-xyz-12345")


def test_fastembed_real_bge_small_model_lazy() -> None:
    embedder = FastEmbedEmbedder("BAAI/bge-small-en-v1.5", lazy_load=True)
    assert embedder.dimension == 384
    q_vec = embedder.embed_query("retrieval test")
    assert isinstance(q_vec, list)
    assert len(q_vec) == 384
    assert all(isinstance(x, float) for x in q_vec)
    d_vecs = embedder.embed_documents(["first document", "second document"])
    assert len(d_vecs) == 2
    assert len(d_vecs[0]) == 384
    assert len(d_vecs[1]) == 384


# --- Service assembly and configuration tests ---


def test_create_embedder_selects_fastembed_by_default() -> None:
    settings = Settings(
        embedding_provider="fastembed",
        embedding_model="BAAI/bge-small-en-v1.5",
    )
    embedder = create_embedder(settings)
    assert isinstance(embedder, FastEmbedEmbedder)
    assert embedder.model_name == "BAAI/bge-small-en-v1.5"
    assert embedder.dimension == 384


def test_create_embedder_selects_sentence_transformers_when_configured() -> None:
    settings = Settings(
        embedding_provider="sentence-transformers",
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    )
    embedder = create_embedder(settings)
    assert isinstance(embedder, SentenceTransformerEmbedder)
    assert embedder.model_name == "sentence-transformers/all-MiniLM-L6-v2"
    assert embedder.dimension == 384


def test_create_embedder_rejects_unsupported_provider() -> None:
    settings = Settings.model_construct(
        embedding_provider="unknown-provider",
        embedding_model="some-model",
        embedding_batch_size=32,
    )
    with pytest.raises(ConfigurationError, match="Unsupported embedding provider"):
        create_embedder(settings)


def test_settings_provider_normalization() -> None:
    s1 = Settings(embedding_provider="FASTEMBED")
    assert s1.embedding_provider == "fastembed"
    s2 = Settings(embedding_provider="SENTENCE_TRANSFORMERS")
    assert s2.embedding_provider == "sentence-transformers"
    s3 = Settings(embedding_provider="sentence-transformers")
    assert s3.embedding_provider == "sentence-transformers"

    with pytest.raises(ValueError, match="Unsupported EMBEDDING_PROVIDER"):
        Settings(embedding_provider="invalid")
