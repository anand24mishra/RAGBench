# Experiment Report: `topk-5`

- **Date:** 2026-09-26 23:27:44 UTC
- **Dataset:** `ragbench-v2-baseline` version `1.0.0`
- **Dataset Fingerprint:** `5eff675854e0f6b57af67128dc6501b1cf0a7cb2add49631218e824ca65c1988`
- **Dataset Scope Notice:** Evaluated on the current 10-question repository-specific benchmark (5 documents). Results indicate behavior on this specific workload and are not broad statistical claims.

## Hypothesis and Parameter Change

- **Hypothesis:** Reference top-k retrieval depth (top_k=5) matching baseline retrieval parameters under the V3 experiment runner.
- **Changed Parameter:** `none (top-k reference)`

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
- **Total evaluation runtime:** 64.80 ms

| Phase | Mean (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Min (ms) | Max (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Query Embedding | 5.976 | 5.867 | 6.616 | 6.620 | 5.472 | 6.621 |
| Vector Retrieval | 0.473 | 0.318 | 1.195 | 1.686 | 0.246 | 1.809 |

## Ranking Changes & Observed Retrieval Failures

No relevant document rank movements observed between baseline and experiment.

Zero retrieval failures: all relevant documents were present within the top-5 results.

## Interpretation and Decision

- **Interpretation:** On the current 10-question repository-specific benchmark, retrieval quality metrics matched baseline exactly. Latency and granularity trade-offs should guide application fit.
- **Decision:** Retain for further investigation

Generation evaluation: Not implemented.
