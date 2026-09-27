# Experiment Report: `embed-paraphrase-minilm-l3-v2`

- **Date:** 2026-09-26 23:28:06 UTC
- **Dataset:** `ragbench-v2-baseline` version `1.0.0`
- **Dataset Fingerprint:** `5eff675854e0f6b57af67128dc6501b1cf0a7cb2add49631218e824ca65c1988`
- **Dataset Scope Notice:** Evaluated on the current 10-question repository-specific benchmark (5 documents). Results indicate behavior on this specific workload and are not broad statistical claims.

## Hypothesis and Parameter Change

- **Hypothesis:** Alternative compact 3-layer MiniLM model (paraphrase-MiniLM-L3-v2, 384 dimensions) provides lower query embedding latency while testing semantic retrieval retention.
- **Changed Parameter:** `embedding_model=sentence-transformers/paraphrase-MiniLM-L3-v2`

## Configuration

| Parameter | Value |
| --- | --- |
| Chunk Size | 800 characters |
| Chunk Overlap | 100 characters |
| Retrieval Depth (top-k) | 5 |
| Embedding Model | `sentence-transformers/paraphrase-MiniLM-L3-v2` |
| Embedding Dimension | 384 |
| Embedding Batch Size | 32 |
| Vector Store | qdrant (memory) |
| Distance Metric | cosine |

## Retrieval Quality Metrics

| Metric | Baseline | Experiment | Delta |
| --- | ---: | ---: | ---: |
| mrr | 0.925000 | 0.950000 | +0.025000 |
| recall_at_1 | 0.900000 | 0.900000 | 0.000000 |
| recall_at_3 | 0.900000 | 1.000000 | +0.100000 |
| recall_at_5 | 1.000000 | 1.000000 | 0.000000 |

## Performance & Latency Measurements

- **Sample size:** 10 queries
- **Total evaluation runtime:** 59.46 ms

| Phase | Mean (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Min (ms) | Max (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Query Embedding | 5.576 | 5.710 | 6.285 | 6.436 | 4.641 | 6.474 |
| Vector Retrieval | 0.342 | 0.320 | 0.453 | 0.485 | 0.295 | 0.493 |

## Ranking Changes & Observed Retrieval Failures

### Observed Rank Movements (1 document changes)

| Query ID | Expected Document | Baseline Rank | Experiment Rank | Baseline Score | Experiment Score |
| --- | --- | ---: | ---: | ---: | ---: |
| `q007` | `generation` | 4 | 2 | 0.2912 | 0.3530 |

Zero retrieval failures: all relevant documents were present within the top-5 results.

## Interpretation and Decision

- **Interpretation:** On the current 10-question repository-specific benchmark, MRR shifted by +0.0250. Directional change is noted, but dataset sample size (10 queries) is not statistically representative.
- **Decision:** Retain for further investigation

Generation evaluation: Not implemented.
