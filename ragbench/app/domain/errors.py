class RAGBenchError(Exception):
    """Base class for errors safe to map at the API boundary."""

    code = "ragbench_error"


class DocumentError(RAGBenchError):
    code = "invalid_document"


class EmptyDocumentError(DocumentError):
    code = "empty_document"


class UnsupportedDocumentTypeError(DocumentError):
    code = "unsupported_document_type"


class DocumentDecodeError(DocumentError):
    code = "document_decode_error"


class EmbeddingError(RAGBenchError):
    code = "embedding_error"


class VectorStoreError(RAGBenchError):
    code = "vector_store_error"


class LLMProviderError(RAGBenchError):
    code = "llm_provider_error"


class LLMTimeoutError(LLMProviderError):
    code = "llm_timeout"


class ConfigurationError(RAGBenchError):
    code = "configuration_error"
