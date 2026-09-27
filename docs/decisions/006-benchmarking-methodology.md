# ADR-006: Benchmarking Methodology and Cold-Start Separation

Status: Accepted for V3 service latency benchmarking

## Context

Embedding models and vector databases exhibit distinct cold-start latencies due to weight loading, graph initialization, and tokenizer setup. Measuring query execution on an unprimed pipeline skews latency reporting (e.g., initial model load taking seconds while steady-state queries take milliseconds).

## Options Considered

- Single-pass un-warmed query timing;
- Aggregate timing across all queries including startup;
- Explicit separation of cold-start model initialization from warmed steady-state query latencies with p50, p95, and p99 percentiles.

## Decision

Measure model initialization duration separately from query execution. In benchmarking runs, execute configurable warm-up repetitions before measuring steady-state latencies. Aggregate query embedding and vector retrieval latencies into arithmetic mean, p50, p95, and p99 percentiles using monotonic high-resolution clocks (`time.perf_counter`). Prominently state the sample size (e.g., 10 questions) in all benchmark artifacts to prevent overstating statistical power on small suites.

## Why

Separating startup from inference provides actionable operational insights: developers can plan container warmup and readiness probes accurately, while observing real latency percentiles during steady-state service operation.

## Trade-offs

Benchmarking requires additional compute iterations to warm up the pipeline. Percentile calculations on small sample sizes (e.g., 10 samples) represent directional distributions rather than high-confidence production percentiles.

## Consequences

Benchmark reports record exact execution environment data (Python version, OS, CPU architecture, detected accelerator) and save structured machine-readable reports in `benchmarks/reports/`.
