# ADR-003: Establish a Retrieval Baseline

Status: Accepted and implemented in V1

## Context

The project needs an interpretable retrieval baseline before evaluating reranking, hybrid search, or prompt changes. V1 does not yet have a relevance dataset.

## Options Considered

- dense vector retrieval;
- lexical retrieval;
- hybrid dense and lexical retrieval; and
- dense retrieval followed by reranking.

## Decision

Use normalized sentence-transformer embeddings and Qdrant cosine top-k retrieval without reranking. The embedding model and default top-k remain configurable.

## Why

A single-stage baseline makes retrieval errors easier to attribute and produces a reference point for later experiments. Adding reranking before relevance labels and baseline metrics would increase complexity without evidence that ranking depth is the current failure.

## Trade-offs

Dense retrieval can match semantic similarity but may miss exact identifiers and rare terms. Lexical retrieval has complementary behavior. Hybrid search and reranking may improve ranking at the cost of configuration, latency, and additional failure modes.

## Consequences

Retrieval returns stable chunk and document IDs, text, metadata, rank order, and Qdrant similarity scores. Top-k defaults to 5 and can be overridden per request. Filters, hybrid retrieval, score thresholds, and reranking remain unimplemented and require explicit experiments.
