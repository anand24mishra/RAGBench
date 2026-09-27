# Ingestion

RAGBench V1 accepts UTF-8 plain-text and Markdown documents. Supported filename extensions are `.txt`, `.md`, and `.markdown`. The loader rejects unsupported extensions, invalid UTF-8, and content containing only whitespace.

The document ID is the SHA-256 digest of the original uploaded bytes. Metadata contains the upload source, base filename, and document ID. The API enforces a configurable upload-size limit before chunking and embedding.
