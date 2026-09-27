# ADR-001: Use Qdrant for Vector Storage

Status: Accepted and implemented in V1

## Context

RAGBench needs a vector index that can run locally, preserve chunk payloads and scores, and remain behind an application interface.

## Options Considered

- an application-owned in-memory index;
- Qdrant running locally or as a service; and
- a managed vector service.

## Decision

Use Qdrant with cosine distance. Run it as a separate service in Docker Compose and isolate Qdrant-specific calls behind `VectorStore`.

## Why

Qdrant provides local Docker operation, an asynchronous Python client, payload storage, and search scores without embedding storage details in the retriever. Its in-memory client also supports deterministic integration tests without a network service.

## Trade-offs

Qdrant adds a service dependency, persistence management, collection lifecycle, and network failure modes. Its approximate indexing behavior may differ from exact in-memory search. A managed service could reduce operations work but would add provider cost and reduce local reproducibility.

## Consequences

Collection size is derived from the embedding model. A dimension mismatch causes startup or ingestion failure rather than automatic migration. Chunk text and metadata are stored as payloads. Docker Compose persists data in `qdrant_data`. Filtering and managed deployment remain outside V1.
