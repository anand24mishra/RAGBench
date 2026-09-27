# ADR-005: Controlled Retrieval Experiments and Isolation

Status: Accepted for V3 retrieval experiments

## Context

To improve retrieval quality and evaluate design trade-offs, engineers must test parameters such as chunk size, overlap, retrieval depth (top-k), and alternative embedding models. If multiple variables change simultaneously or if vector indices contaminate across runs, observed score changes cannot be attributed to a specific cause.

## Options Considered

- Ad-hoc scripts modifying global pipeline configuration;
- Single configuration file overwritten before each run;
- Machine-readable typed experiment configuration with strict single-variable change enforcement and isolated in-memory vector collections per run.

## Decision

Adopt typed, validated YAML experiment configurations stored under `experiments/` (`chunking/`, `top_k/`, `embeddings/`) and indexed in `experiments/registry.yaml`. Enforce that each candidate experiment modifies at most one parameter family relative to the baseline. Isolate every run into a dedicated in-memory Qdrant collection to prevent cross-experiment embedding contamination.

## Why

Single-variable control provides scientific attribution: differences in Recall@K, MRR, or latency are directly attributable to the changed parameter. Isolated collections eliminate cache bleed and cross-vector interference.

## Trade-offs

Parameter co-optimization (e.g., tuning chunk size jointly with top-k) is restricted to sequential exploration steps rather than simultaneous combinatorial grid changes.

## Consequences

Every experiment generates its own machine-readable JSON artifact and human-readable Markdown report in `evaluation/reports/` without altering or overwriting `baseline.json`. Automated comparison verifies identical dataset version, dataset fingerprint, and query count, while reporting signed metric and latency deltas as well as individual document rank movements.
