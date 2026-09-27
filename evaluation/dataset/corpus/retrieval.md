# Retrieval

RAGBench V1 uses dense semantic retrieval. The same configured sentence-transformer model embeds documents and queries, and embeddings are normalized. Qdrant stores chunk vectors and performs cosine-distance search.

The retriever returns the top-k chunks in Qdrant rank order with chunk ID, document ID, text, metadata, and similarity score. The default top-k is 5. V1 does not implement lexical search, hybrid retrieval, metadata filtering, a score threshold, or reranking.
