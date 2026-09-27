# Experiment Report: `topk-10`

- **Date:** 2026-09-26 23:27:51 UTC
- **Dataset:** `ragbench-v2-baseline` version `1.0.0`
- **Dataset Fingerprint:** `5eff675854e0f6b57af67128dc6501b1cf0a7cb2add49631218e824ca65c1988`
- **Dataset Scope Notice:** Evaluated on the current 10-question repository-specific benchmark (5 documents). Results indicate behavior on this specific workload and are not broad statistical claims.

## Hypothesis and Parameter Change

- **Hypothesis:** Increasing retrieval depth to top_k=10 retrieves deeper candidates to safeguard recall, measuring the latency and candidate overhead on this workload.
- **Changed Parameter:** `top_k=10`

## Configuration

| Parameter | Value |
| --- | --- |
| Chunk Size | 800 characters |
| Chunk Overlap | 100 characters |
| Retrieval Depth (top-k) | 10 |
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
- **Total evaluation runtime:** 59.06 ms

| Phase | Mean (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Min (ms) | Max (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Query Embedding | 5.603 | 5.639 | 6.096 | 6.259 | 4.763 | 6.300 |
| Vector Retrieval | 0.278 | 0.248 | 0.407 | 0.486 | 0.240 | 0.506 |

## Ranking Changes & Observed Retrieval Failures

No relevant document rank movements observed between baseline and experiment.

Zero retrieval failures: all relevant documents were present within the top-10 results.

## Interpretation and Decision

- **Interpretation:** On the current 10-question repository-specific benchmark, retrieval quality metrics matched baseline exactly. Latency and granularity trade-offs should guide application fit.
- **Decision:** Retain for further investigation

Generation evaluation: Not implemented.
