from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ragbench.app.domain.errors import EmbeddingError


class Embedder(ABC):
    @property
    @abstractmethod
    def dimension(self) -> int: ...

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    @abstractmethod
    def embed_query(self, text: str) -> list[float]: ...


class SentenceTransformerEmbedder(Embedder):
    def __init__(
        self,
        model_name: str,
        *,
        batch_size: int = 32,
        model: Any | None = None,
    ) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero")
        self.model_name = model_name
        self.batch_size = batch_size
        if model is None:
            try:
                from sentence_transformers import SentenceTransformer

                model = SentenceTransformer(model_name)
            except Exception as exc:
                raise EmbeddingError(f"Failed to load embedding model '{model_name}'") from exc
        self._model = model
        get_dimension = getattr(self._model, "get_embedding_dimension", None)
        if get_dimension is None:
            get_dimension = self._model.get_sentence_embedding_dimension
        dimension = get_dimension()
        if not dimension:
            raise EmbeddingError("Embedding model did not report a vector dimension")
        self._dimension = int(dimension)

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if any(not text.strip() for text in texts):
            raise EmbeddingError("Documents passed for embedding must not be empty")
        try:
            vectors = self._model.encode(
                texts,
                batch_size=self.batch_size,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            result = vectors.tolist()
        except Exception as exc:
            raise EmbeddingError("Document embedding failed") from exc
        if len(result) != len(texts) or any(len(vector) != self.dimension for vector in result):
            raise EmbeddingError("Embedding model returned an unexpected output shape")
        return result

    def embed_query(self, text: str) -> list[float]:
        if not text.strip():
            raise EmbeddingError("Query passed for embedding must not be empty")
        return self.embed_documents([text])[0]


class FastEmbedEmbedder(Embedder):
    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
        *,
        batch_size: int = 32,
        model: Any | None = None,
        lazy_load: bool = True,
    ) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero")
        self.model_name = model_name
        self.batch_size = batch_size
        if model is None:
            try:
                from fastembed import TextEmbedding

                try:
                    model = TextEmbedding(model_name=model_name, lazy_load=lazy_load)
                except TypeError:
                    model = TextEmbedding(model_name=model_name)
            except Exception as exc:
                raise EmbeddingError(f"Failed to load embedding model '{model_name}'") from exc
        self._model = model

        dimension = getattr(self._model, "embedding_size", None)
        if dimension is None:
            dimension = getattr(self._model, "dimension", None)
        if dimension is None:
            get_dim = getattr(self._model, "get_embedding_dimension", None)
            if callable(get_dim):
                dimension = get_dim()
        if dimension is None:
            get_sentence_dim = getattr(self._model, "get_sentence_embedding_dimension", None)
            if callable(get_sentence_dim):
                dimension = get_sentence_dim()
        if dimension is None:
            get_size = getattr(self._model, "get_embedding_size", None)
            if callable(get_size):
                try:
                    dimension = get_size(model_name)
                except Exception:
                    pass
        if not dimension:
            raise EmbeddingError("Embedding model did not report a vector dimension")
        self._dimension = int(dimension)

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if any(not text.strip() for text in texts):
            raise EmbeddingError("Documents passed for embedding must not be empty")
        try:
            embeddings_iter = self._model.embed(texts, batch_size=self.batch_size)
            result = [
                vec.tolist() if hasattr(vec, "tolist") else [float(x) for x in vec]
                for vec in embeddings_iter
            ]
        except Exception as exc:
            raise EmbeddingError("Document embedding failed") from exc
        if len(result) != len(texts) or any(len(vector) != self.dimension for vector in result):
            raise EmbeddingError("Embedding model returned an unexpected output shape")
        return result

    def embed_query(self, text: str) -> list[float]:
        if not text.strip():
            raise EmbeddingError("Query passed for embedding must not be empty")
        return self.embed_documents([text])[0]
