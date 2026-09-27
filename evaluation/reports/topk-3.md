# Experiment Report: `topk-3`

- **Date:** 2026-09-26 23:27:38 UTC
- **Dataset:** `ragbench-v2-baseline` version `1.0.0`
- **Dataset Fingerprint:** `5eff675854e0f6b57af67128dc6501b1cf0a7cb2add49631218e824ca65c1988`
- **Dataset Scope Notice:** Evaluated on the current 10-question repository-specific benchmark (5 documents). Results indicate behavior on this specific workload and are not broad statistical claims.

## Hypothesis and Parameter Change

- **Hypothesis:** Retrieving top_k=3 candidates reduces candidate context size and latency compared to top_k=5, but fails queries whose evidence appears at ranks 4 or 5.
- **Changed Parameter:** `top_k=3`

## Configuration

| Parameter | Value |
| --- | --- |
| Chunk Size | 800 characters |
| Chunk Overlap | 100 characters |
| Retrieval Depth (top-k) | 3 |
| Embedding Model | `sentence-transformers/all-MiniLM-L6-v2` |
| Embedding Dimension | 384 |
| Embedding Batch Size | 32 |
| Vector Store | qdrant (memory) |
| Distance Metric | cosine |

## Retrieval Quality Metrics

| Metric | Baseline | Experiment | Delta |
| --- | ---: | ---: | ---: |
| mrr | 0.925000 | 0.900000 | -0.025000 |
| recall_at_1 | 0.900000 | 0.900000 | 0.000000 |
| recall_at_3 | 0.900000 | 0.900000 | 0.000000 |
| recall_at_5 | 1.000000 | 0.900000 | -0.100000 |

> **Note on Top-k semantics:** When retrieval depth top_k is configured below 5, the candidate pool is capped at 3 chunks. Metrics Recall@3 and Recall@5 are calculated on the retrieved candidate set; because fewer than 5 items are retrieved, relevant items outside the retrieved top_k cannot be recalled at cutoff 5.

## Performance & Latency Measurements

- **Sample size:** 10 queries
- **Total evaluation runtime:** 115.44 ms

| Phase | Mean (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Min (ms) | Max (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Query Embedding | 10.850 | 9.551 | 18.315 | 22.016 | 7.369 | 22.941 |
| Vector Retrieval | 0.601 | 0.382 | 1.317 | 1.423 | 0.335 | 1.449 |

## Ranking Changes & Observed Retrieval Failures

### Observed Rank Movements (1 document changes)

| Query ID | Expected Document | Baseline Rank | Experiment Rank | Baseline Score | Experiment Score |
| --- | --- | ---: | ---: | ---: | ---: |
| `q007` | `generation` | 4 | Not in top-k | 0.2912 | N/A |

### Unretrieved Documents at top_k=3 (1 failures)

| Query ID | Missing Expected Document | Retrieved Document Candidates |
| --- | --- | --- |
| `q007` | `generation` | `chunking`, `retrieval`, `observability` |

## Interpretation and Decision

- **Interpretation:** On the current 10-question repository-specific benchmark, Recall@5 degraded by 0.1000. The candidate configuration dropped previously retrieved evidence.
- **Decision:** Reject for this workload

Generation evaluation: Not implemented.
