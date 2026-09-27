# Experiment Report: `topk-1`

- **Date:** 2026-09-26 23:27:33 UTC
- **Dataset:** `ragbench-v2-baseline` version `1.0.0`
- **Dataset Fingerprint:** `5eff675854e0f6b57af67128dc6501b1cf0a7cb2add49631218e824ca65c1988`
- **Dataset Scope Notice:** Evaluated on the current 10-question repository-specific benchmark (5 documents). Results indicate behavior on this specific workload and are not broad statistical claims.

## Hypothesis and Parameter Change

- **Hypothesis:** Restricting retrieval to top_k=1 minimizes candidate count and search latency, but drops recall whenever the relevant passage is ranked lower than first.
- **Changed Parameter:** `top_k=1`

## Configuration

| Parameter | Value |
| --- | --- |
| Chunk Size | 800 characters |
| Chunk Overlap | 100 characters |
| Retrieval Depth (top-k) | 1 |
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

> **Note on Top-k semantics:** When retrieval depth top_k is configured below 5, the candidate pool is capped at 1 chunks. Metrics Recall@3 and Recall@5 are calculated on the retrieved candidate set; because fewer than 5 items are retrieved, relevant items outside the retrieved top_k cannot be recalled at cutoff 5.

## Performance & Latency Measurements

- **Sample size:** 10 queries
- **Total evaluation runtime:** 64.64 ms

| Phase | Mean (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Min (ms) | Max (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Query Embedding | 6.174 | 6.256 | 6.778 | 6.911 | 5.616 | 6.944 |
| Vector Retrieval | 0.272 | 0.262 | 0.331 | 0.366 | 0.250 | 0.374 |

## Ranking Changes & Observed Retrieval Failures

### Observed Rank Movements (1 document changes)

| Query ID | Expected Document | Baseline Rank | Experiment Rank | Baseline Score | Experiment Score |
| --- | --- | ---: | ---: | ---: | ---: |
| `q007` | `generation` | 4 | Not in top-k | 0.2912 | N/A |

### Unretrieved Documents at top_k=1 (1 failures)

| Query ID | Missing Expected Document | Retrieved Document Candidates |
| --- | --- | --- |
| `q007` | `generation` | `chunking` |

## Interpretation and Decision

- **Interpretation:** On the current 10-question repository-specific benchmark, Recall@5 degraded by 0.1000. The candidate configuration dropped previously retrieved evidence.
- **Decision:** Reject for this workload

Generation evaluation: Not implemented.
