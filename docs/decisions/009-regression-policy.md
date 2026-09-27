# ADR-009: Regression Detection Engine and Multi-Dimensional Gate Policy

Status: Accepted for V5 regression detection and CI quality gating

## Context

When modifying ingestion chunking, embedding models, vector search top-k, or prompt templates, engineering teams need to verify whether quality improved without unacceptable latency, cost, or reliability regressions. Reducing these distinct engineering trade-offs into a single weighted score obscures critical regressions.

## Options Considered

- **Single Weighted Overall Score**: Combine retrieval metrics, correctness, latency, and cost into a composite index (e.g. `0.4*MRR + 0.3*corr - 0.2*lat - 0.1*cost`).
- **Manual Visual Diff Inspection**: Rely exclusively on human inspection of Markdown tables.
- **Configurable Multi-Dimensional Regression Policy with Explicit Tri-State Decisions**: Evaluate each dimension (quality, latency, cost, reliability) against configurable thresholds, outputting structured decisions (`pass`, `fail`, `inconclusive`).

## Decision

1. Implement `evaluate_regression()` comparing candidate evaluation results against versioned baselines.
2. Evaluate across five distinct dimensions:
   - **Retrieval Quality**: Recall@1, Recall@3, Recall@5, MRR minimum deltas.
   - **Generation Quality**: Correctness, faithfulness, context relevance minimum deltas.
   - **Latency**: P95 retrieval/end-to-end relative increase thresholds.
   - **Cost**: Cost per query relative increase thresholds.
   - **Reliability**: Maximum failure rate and timeout tolerances.
3. Emit tri-state decisions:
   - `pass`: all evaluated checks meet configured policy thresholds.
   - `fail`: one or more checks violate policy thresholds.
   - `inconclusive`: required measurements are unavailable or dataset versions mismatch.
4. Produce per-query regression diagnostics isolating which queries suffered rank drops or quality degradation.

## Reasoning

A composite scalar score allows serious regressions (e.g. 5x latency increase or 50% cost explosion) to be masked by minor metric improvements. Separating checks makes every regression actionable. The `inconclusive` state prevents false confidence when datasets or metrics mismatch.

## Trade-offs

Requires maintaining baseline reports and tuning thresholds appropriately to avoid flaky CI gates on small sample sizes.

## Consequences

The `ragbench.regression_gate` CLI provides standard exit codes (0 for pass, 1 for fail, 2 for inconclusive) and generates structured JSON and Markdown audit reports for automated CI quality gating.
