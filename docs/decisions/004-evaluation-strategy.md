# ADR-004: Make Stage-Level Evaluation the Comparison Unit

Status: Accepted for retrieval evaluation in V2; generation evaluation remains planned

## Context

Final-answer quality alone cannot identify whether a regression originates in retrieval, context construction, or generation. V1 had no dataset, metrics, evaluation code, or CI gate.

## Options Considered

- final-answer review only;
- deterministic retrieval metrics plus reference-based answer metrics;
- LLM-as-judge evaluation; and
- a combined stage-level suite with deterministic and judged metrics.

## Decision

Use versioned document-level relevance labels, deterministic Recall@1/3/5 and MRR, and retained per-query artifacts. Generation metrics will be added only when their scoring procedure is explicit and tested. An LLM judge is not part of V2.

## Why

Stage-level results make regressions attributable. Deterministic retrieval metrics are suitable for testing metric code and comparing retriever configurations when relevance labels exist. Judge-based scores can cover qualities that simple string comparisons miss, but they introduce model and prompt variance.

## Trade-offs

Relevance annotation requires manual effort and can be incomplete. Reference-based answer metrics may penalize valid alternatives. LLM judges add cost, latency, parsing failures, and bias. Retaining per-example data improves diagnosis but raises storage and sensitive-data concerns.

## Consequences

Every V2 run identifies the dataset version and fingerprint, retriever configuration, model, software versions, metrics, per-query rankings, and top-k failures. Comparison requires the same dataset version, query count, and metric set. Automated thresholds and CI behavior remain undecided. The repository is not Git-initialized, so reports cannot yet record a code revision.
