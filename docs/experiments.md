# Experiments

## Experiment register

| Experiment ID | Date | Parameter Changed | Status | Recall@1 | Recall@3 | Recall@5 | MRR | Result Artifact |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| `v2-baseline` | 2026-09-26 UTC | None (V1 reference) | Complete | 0.900000 | 0.900000 | 1.000000 | 0.925000 | `evaluation/reports/baseline.json` |
| `chunk-400-50` | 2026-09-26 UTC | `chunk_size=400, overlap=50` | Complete | 0.900000 | 1.000000 | 1.000000 | 0.950000 | `evaluation/reports/chunk-400-50.json` |
| `chunk-800-100` | 2026-09-26 UTC | None (chunking reference) | Complete | 0.900000 | 0.900000 | 1.000000 | 0.925000 | `evaluation/reports/chunk-800-100.json` |
| `chunk-1200-150` | 2026-09-26 UTC | `chunk_size=1200, overlap=150` | Complete | 0.900000 | 0.900000 | 1.000000 | 0.925000 | `evaluation/reports/chunk-1200-150.json` |
| `topk-1` | 2026-09-26 UTC | `top_k=1` | Complete | 0.900000 | 0.900000 | 0.900000 | 0.900000 | `evaluation/reports/topk-1.json` |
| `topk-3` | 2026-09-26 UTC | `top_k=3` | Complete | 0.900000 | 0.900000 | 0.900000 | 0.900000 | `evaluation/reports/topk-3.json` |
| `topk-5` | 2026-09-26 UTC | None (top-k reference) | Complete | 0.900000 | 0.900000 | 1.000000 | 0.925000 | `evaluation/reports/topk-5.json` |
| `topk-10` | 2026-09-26 UTC | `top_k=10` | Complete | 0.900000 | 0.900000 | 1.000000 | 0.925000 | `evaluation/reports/topk-10.json` |
| `embed-all-minilm-l6-v2` | 2026-09-26 UTC | None (embedding reference) | Complete | 0.900000 | 0.900000 | 1.000000 | 0.925000 | `evaluation/reports/embed-all-minilm-l6-v2.json` |
| `embed-paraphrase-minilm-l3-v2` | 2026-09-26 UTC | `embedding_model=...paraphrase-MiniLM-L3-v2` | Complete | 0.900000 | 1.000000 | 1.000000 | 0.950000 | `evaluation/reports/embed-paraphrase-minilm-l3-v2.json` |

## Controlled Experiment Principle

Every experiment varies **ONE parameter family** at a time against the baseline configuration while holding fixed:
- Dataset: `ragbench-v2-baseline` version `1.0.0` (SHA-256: `5eff675854e0f6b57af67128dc6501b1cf0a7cb2add49631218e824ca65c1988`)
- Corpus: 5 documents (`chunking.md`, `generation.md`, `ingestion.md`, `observability.md`, `retrieval.md`)
- Questions: 10 hand-authored questions (`q001` through `q010`)
- Metric evaluation methodology: document-level Recall@1, Recall@3, Recall@5, MRR

The runner verifies that candidate configurations do not alter multiple parameters simultaneously. If an experiment attempts to change both chunking and top-k or embedding model, it raises a `ControlledExperimentError`.

---

## EXP-001: Baseline Reference

- **Experiment ID:** `v2-baseline`
- **Hypothesis:** Establish retrieval reference for the 10-question evaluation dataset using standard pipeline parameters.
- **Changed Parameter:** None
- **Configuration:** chunk_size=800, chunk_overlap=100, top_k=5, model=`sentence-transformers/all-MiniLM-L6-v2`
- **Metrics:** Recall@1: 0.900000, Recall@3: 0.900000, Recall@5: 1.000000, MRR: 0.925000
- **Interpretation:** High recall on direct questions; `q007` placed target evidence at rank 4.
- **Decision:** Retain as the permanent fixed baseline reference.

---

## EXP-002: Chunking Family

Tests character chunk sizing and overlap:
- `chunk-400-50`: chunk_size=400, overlap=50
- `chunk-800-100`: chunk_size=800, overlap=100 (reference)
- `chunk-1200-150`: chunk_size=1200, overlap=150

### Measured Results

| Experiment ID | Chunk / Overlap | Recall@1 | Recall@3 | Recall@5 | MRR | Query Emb Latency (mean/p50/p95) | Retrieval Latency (mean/p50/p95) |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `chunk-400-50` | 400 / 50 | 0.900000 | 1.000000 | 1.000000 | 0.950000 | 14.46ms / 13.26ms / 28.11ms | 0.88ms / 0.31ms / 3.55ms |
| `chunk-800-100` | 800 / 100 | 0.900000 | 0.900000 | 1.000000 | 0.925000 | 9.30ms / 8.81ms / 13.91ms | 0.44ms / 0.28ms / 1.48ms |
| `chunk-1200-150` | 1200 / 150 | 0.900000 | 0.900000 | 1.000000 | 0.925000 | 7.33ms / 6.95ms / 11.23ms | 0.32ms / 0.28ms / 0.48ms |

### Observed Ranking Movements
- `chunk-400-50`: `q007` relevant document `generation` moved from **rank 4 to rank 1** (score 0.2912 -> 0.5402), raising Recall@3 to 1.0 and MRR to 0.9500. `q002` moved from rank 1 to rank 2.
- `chunk-1200-150`: No rank movements relative to baseline ranks 1 through 5.

**Interpretation:** On the current 10-question repository-specific benchmark, 400-character chunking brought target evidence into the top-3 for `q007`. However, with only 10 questions, this directional difference is not statistically representative.
**Decision:** Retain for further investigation.

---

## EXP-003: Retrieval Depth (Top-K) Family

Tests candidate retrieval cutoff:
- `topk-1`: top_k=1
- `topk-3`: top_k=3
- `topk-5`: top_k=5 (reference)
- `topk-10`: top_k=10

### Measured Results

| Experiment ID | Top-K | Recall@1 | Recall@3 | Recall@5 | MRR | Returned Candidates | Failures at Cutoff | Retrieval Latency (mean/p50/p95) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `topk-1` | 1 | 0.900000 | 0.900000 | 0.900000 | 0.900000 | 1 | 1 (`q007`) | 0.27ms / 0.26ms / 0.34ms |
| `topk-3` | 3 | 0.900000 | 0.900000 | 0.900000 | 0.900000 | 3 | 1 (`q007`) | 0.60ms / 0.38ms / 1.32ms |
| `topk-5` | 5 | 0.900000 | 0.900000 | 1.000000 | 0.925000 | 5 | 0 | 0.47ms / 0.46ms / 0.72ms |
| `topk-10` | 10 | 0.900000 | 0.900000 | 1.000000 | 0.925000 | 10 | 0 | 0.28ms / 0.26ms / 0.38ms |

### Top-K Metric Semantics
When retrieval depth top_k is configured below 5 (e.g. `topk-1`, `topk-3`), the retriever fetches at most top_k candidates. Metrics Recall@3 and Recall@5 evaluate whether target documents were recalled within the retrieved candidates. Because candidate depth is capped at K, items ranked below K cannot be recalled at cutoff 5, reflecting the real operational impact of shallow retrieval.

### Observed Ranking Movements
- For both `topk-1` and `topk-3`, `q007` (ranked 4th in baseline) is omitted from the retrieved candidates. This resulted in 1 retrieval failure and dropped Recall@5 to 0.900000 and MRR to 0.900000.

**Interpretation:** On this dataset, setting top-k below 4 causes context truncation for queries requiring deeper semantic matching.
**Decision:** Reject `topk-1` and `topk-3` for this workload. Retain `topk-5` as adequate retrieval depth.

---

## EXP-004: Embedding Model Family

Tests alternative dense embedding architectures:
- `embed-all-minilm-l6-v2`: `sentence-transformers/all-MiniLM-L6-v2` (6 layers, 384 dimensions)
- `embed-paraphrase-minilm-l3-v2`: `sentence-transformers/paraphrase-MiniLM-L3-v2` (3 layers, 384 dimensions)

### Measured Results

| Experiment ID | Model Name | Dim | Recall@1 | Recall@3 | Recall@5 | MRR | Query Emb Latency (mean/p50/p95) | Retrieval Latency (mean/p50/p95) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `embed-all-minilm-l6-v2` | `all-MiniLM-L6-v2` | 384 | 0.900000 | 0.900000 | 1.000000 | 0.925000 | 5.98ms / 5.51ms / 9.87ms | 0.31ms / 0.30ms / 0.40ms |
| `embed-paraphrase-minilm-l3-v2` | `paraphrase-MiniLM-L3-v2` | 384 | 0.900000 | 1.000000 | 1.000000 | 0.950000 | 5.58ms / 5.25ms / 9.28ms | 0.34ms / 0.32ms / 0.47ms |

### Observed Ranking Movements
- In `embed-paraphrase-minilm-l3-v2`, `q007` moved from **rank 4 to rank 1** (score 0.2912 -> 0.4285), and `q008` moved from rank 1 to rank 2, producing Recall@3=1.000000 and MRR=0.950000.

**Interpretation:** The 3-layer model demonstrated competitive retrieval precision while reducing computational depth. Model initialization and inference require less memory.
**Decision:** Retain for further investigation on larger evaluation benchmarks.

---

## EXP-005: Cost vs Quality Trade-off Experimentation

RAGBench V5 introduces infrastructure (`ragbench.experiments.cost_vs_quality`) to systematically compare:

- **Configuration A**: Lower-cost, high-speed model (e.g. `gpt-4o-mini`)
- **Configuration B**: Higher-cost model (e.g. `gpt-4o`)

### Trade-off Evaluation Dimensions

1. **Answer Quality**: Correctness, Faithfulness / Groundedness, Context Relevance
2. **Inference Latency**: Mean and P95 generation latency
3. **Token Consumption**: Input tokens, output tokens, total tokens
4. **Economic Cost**: Total run cost and cost per query derived from `data/pricing.yaml`

### Decision Principle

The framework rejects naive single-variable optimization:
- Never automatically choose the cheapest model if it compromises factual correctness or hallucination rates.
- Never automatically choose the highest-parameter model if it introduces unacceptable latency or disproportionate cost (e.g. 10x cost for 2% correctness delta).
- Expose the Pareto frontier to enable deliberate, policy-driven trade-offs.

---

## Running Experiments

Execute a single controlled retrieval experiment:

```bash
python -m ragbench.experiments run experiments/chunking/400_50.yaml
```

Compare any two result artifacts:

```bash
python -m ragbench.experiments compare evaluation/reports/baseline.json evaluation/reports/chunk-400-50.json
```

Benchmark configuration latency:

```bash
python -m ragbench.experiments benchmark experiments/baseline/config.yaml --warmup 2 --runs 5
```

Execute Generation Quality Evaluation:

```bash
python -m ragbench.eval_generation \
  --questions evaluation/dataset/v1.1.0/questions.jsonl \
  --metadata evaluation/dataset/v1.1.0/metadata.json \
  --corpus evaluation/dataset/corpus \
  --result-path evaluation/reports/generation_v5_candidate.json \
  --summary-path evaluation/reports/generation_v5_candidate.md
```

Execute Regression Detection Gate:

```bash
python -m ragbench.regression_gate \
  --baseline evaluation/reports/generation_v4_baseline.json \
  --candidate evaluation/reports/generation_v5_candidate.json \
  --output-json evaluation/reports/regression_v5_decision.json \
  --output-md evaluation/reports/regression_v5_report.md
```

List registered experiments:

```bash
python -m ragbench.experiments list
```

Run all registered experiments:

```bash
python -m ragbench.experiments run-all
```

