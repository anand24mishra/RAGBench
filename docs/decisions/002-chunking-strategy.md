# ADR-002: Establish a Chunking Baseline

Status: Accepted and implemented in V1

## Context

Chunk boundaries affect recall, context precision, embedding cost, and the evidence available to generation. V1 needs a deterministic baseline before a quality dataset exists.

## Options Considered

- fixed-size chunks with overlap;
- sentence or paragraph-aware chunks;
- recursive structural splitting; and
- semantic chunking.

## Decision

Use fixed-size character chunks with configurable size and overlap. Defaults are 800 characters and 100 characters. Keep structural and semantic alternatives for later controlled experiments.

## Why

Fixed-size chunking provides a transparent baseline with few parameters. It makes boundary behavior reproducible and allows size and overlap to be varied independently. This is a methodology choice, not a claim that fixed-size chunking will produce the best retrieval quality.

## Trade-offs

Fixed boundaries can split sentences, tables, or related evidence. Overlap can reduce boundary loss but increases index size and can produce duplicate retrieval. Structural and semantic methods may preserve meaning better but introduce parser or model dependencies and additional configuration.

## Consequences

Chunk IDs are derived from document ID and character offsets. Metadata records index and offsets. Unit tests cover empty, short, exact-size, long, and overlapping input. The strategy can split semantic units, so it should be treated as a baseline rather than an optimum.
