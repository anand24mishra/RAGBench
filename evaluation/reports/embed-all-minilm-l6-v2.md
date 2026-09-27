# Experiment Report: `embed-all-minilm-l6-v2`

- **Date:** 2026-09-26 23:27:58 UTC
- **Dataset:** `ragbench-v2-baseline` version `1.0.0`
- **Dataset Fingerprint:** `5eff675854e0f6b57af67128dc6501b1cf0a7cb2add49631218e824ca65c1988`
- **Dataset Scope Notice:** Evaluated on the current 10-question repository-specific benchmark (5 documents). Results indicate behavior on this specific workload and are not broad statistical claims.

## Hypothesis and Parameter Change

- **Hypothesis:** Baseline embedding model reference (sentence-transformers/all-MiniLM-L6-v2, 384 dimensions) under the V3 experiment runner.
- **Changed Parameter:** `none (embedding reference)`

## Configuration

| Parameter | Value |
| --- | --- |
| Chunk Size | 800 characters |
| Chunk Overlap | 100 characters |
| Retrieval Depth (top-k) | 5 |
| Embedding Model | `sentence-transformers/all-MiniLM-L6-v2` |
| Embedding Dimension | 384 |
| Embedding Batch Size | 32 |
| Vector Store | qdrant (memory) |
| Distance Metric | cosine |

## Retrieval Quality Metrics

| Metric | Baseline | Experiment | Delta |
| --- | ---: | ---: | ---: |
| mrr | 0.925000 | 0.925000 | 0.000000 |
| recall_at_1 | 0.900000 | 0.900000 | 0.000000 |
| recall_at_3 | 0.900000 | 0.900000 | 0.000000 |
| recall_at_5 | 1.000000 | 1.000000 | 0.000000 |

## Performance & Latency Measurements

- **Sample size:** 10 queries
- **Total evaluation runtime:** 63.27 ms

| Phase | Mean (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Min (ms) | Max (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Query Embedding | 5.984 | 5.954 | 6.413 | 6.434 | 5.354 | 6.439 |
| Vector Retrieval | 0.313 | 0.275 | 0.483 | 0.604 | 0.265 | 0.634 |

## Ranking Changes & Observed Retrieval Failures

No relevant document rank movements observed between baseline and experiment.

Zero retrieval failures: all relevant documents were present within the top-5 results.

## Interpretation and Decision

- **Interpretation:** On the current 10-question repository-specific benchmark, retrieval quality metrics matched baseline exactly. Latency and granularity trade-offs should guide application fit.
- **Decision:** Retain for further investigation

Generation evaluation: Not implemented.
