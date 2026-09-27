# Evaluation

## Status

V2 implements a versioned retrieval dataset, dataset validation, document-level Recall@1, Recall@3, Recall@5, MRR, per-query retrieval artifacts, missed-document records, JSON and Markdown reports, and result comparison.

V3 extends this framework with:
- stage-level query latency capture (embedding latency, vector search latency, total query runtime);
- latency distribution statistics (mean, p50, p95, p99, min, max);
- per-query document rank movement tracking between baseline and candidate experiments;
- typed experiment configuration with strict single-variable change enforcement; and
- independent vector index isolation per experiment.

V4 extends this framework with:
- versioned evaluation dataset 1.1.0 with 28 questions and corpus-grounded `required_facts`;
- deterministic answer correctness evaluation via normalized fact satisfaction;
- deterministic faithfulness / groundedness evaluation via claim-to-context token containment;
- context relevance evaluation measuring target evidence density in retrieved chunks;
- decoupled, pluggable LLM-as-a-judge evaluation with structured JSON output;
- generation latency measurements with percentiles (p50, p95, p99); and
- failure taxonomy classifying retrieval, context, generation, grounding, and provider errors.

Statistical hypothesis testing, automated CI deployment quality gates, and large-scale external evaluation remain planned.

## Evaluation dataset

### Version 1.0.0 (Retrieval Baseline)

The `ragbench-v2-baseline` dataset contains:

- five Markdown documents under `evaluation/dataset/corpus`;
- ten questions in `evaluation/dataset/questions.jsonl`; and
- dataset name, version, and allowed document IDs in `evaluation/dataset/metadata.json`.

Every question has a stable ID, question text, one or more relevant logical document IDs, and a reference answer.

### Version 1.1.0 (Generation Quality Benchmark)

The `ragbench-v4-generation` dataset contains:

- five Markdown documents under `evaluation/dataset/corpus`;
- 28 questions in `evaluation/dataset/v1.1.0/questions.jsonl`; and
- metadata in `evaluation/dataset/v1.1.0/metadata.json`.

Each record extends the schema with `required_facts`: a list of non-empty factual claims manually derived from the benchmark corpus documents (`chunking.md`, `generation.md`, `ingestion.md`, `observability.md`, `retrieval.md`).

### Creation methodology

The corpus was written from verified V1 behavior and covers five separate responsibilities: ingestion, chunking, retrieval, generation, and observability. Questions were written manually after the documents. A document was labeled relevant when it directly contains the evidence needed to answer the question.

The initial questions are intentionally narrow and mostly use one relevant document. This makes metric behavior and regressions easy to inspect, but it also creates lexical overlap and does not represent an external workload. The author of the implementation also created the relevance labels, so independent annotation has not occurred.

Dataset loading rejects:

- invalid JSONL;
- unknown or extra fields;
- blank IDs or questions;
- empty, blank, or duplicate relevance IDs;
- duplicate question IDs;
- references to documents absent from metadata; and
- an empty question file.

The runner verifies that corpus filename stems exactly match the metadata document IDs. It records a SHA-256 fingerprint over metadata, questions, and ordered corpus files plus a mapping from logical IDs to the production loader's content-derived IDs.

### Preprocessing

No text preprocessing is applied outside the production V1 pipeline. Each corpus file is loaded as UTF-8 Markdown, chunked with the baseline character chunker, embedded using the configured sentence-transformer, and indexed through the Qdrant adapter.

## Retrieval execution

The evaluator does not duplicate retrieval. It constructs the V1 `SemanticRetriever` with the configured embedder and Qdrant store, then calls `retrieve` for every question. The baseline uses Qdrant's in-memory client to avoid dependence on a separately running service while preserving the same application adapter and cosine-search path.

Retrieved chunks are retained with rank, logical document ID, raw content-derived document ID, chunk ID, and score. Since evaluation labels are document-level, repeated chunks from one document are collapsed by document ID in first-occurrence order before rank cutoffs are applied.

## Retrieval metrics

Let \(R_q\) be the set of relevant document IDs for query \(q\), and let \(D_q^k\) be the first \(k\) unique retrieved document IDs.

### Recall@K

```text
Recall@K(q) = |R_q intersect D_q^k| / |R_q|
```

The runner calculates Recall@1, Recall@3, and Recall@5 for each query, then reports the arithmetic mean across queries. A query with no retrieved documents receives zero. The dataset validator prevents an empty relevant set.

#### Top-K Cutoff Semantics
When an experiment configures retrieval depth `top_k < 5` (such as `topk-1` or `topk-3`), the retriever fetches at most `top_k` candidate chunks. Metrics Recall@3 and Recall@5 evaluate whether target documents were recalled within the retrieved candidates. Because candidate depth is capped at K, items ranked below K cannot be recalled at cutoff 5, reflecting the real operational impact of shallow retrieval.

### Reciprocal rank and MRR

Reciprocal rank is `1 / rank` for the first relevant unique document, or zero if no relevant document is retrieved. MRR is the arithmetic mean of reciprocal rank across all questions.

MRR emphasizes the first relevant result. It does not reward retrieving additional relevant documents after the first.

## Running evaluations and experiments

### Run the V2 baseline
From the repository root:

```bash
python -m ragbench.eval
```

The default configuration is `experiments/baseline/config.yaml`.

### Run a controlled V3 experiment
Execute a candidate experiment configuration:

```bash
python -m ragbench.experiments run experiments/chunking/400_50.yaml
```

The runner:
1. validates configuration and ensures at most one parameter family varies from baseline;
2. verifies dataset records and dataset fingerprint;
3. indexes the corpus into a dedicated, isolated in-memory Qdrant collection;
4. invokes the production retriever for every question while capturing stage-level latency;
5. calculates per-query and aggregate Recall@1/3/5, MRR, and latency percentiles (p50, p95, p99);
6. compares metrics against baseline to record signed deltas and document rank movements; and
7. writes machine-readable JSON (`evaluation/reports/<id>.json`) and human-readable Markdown (`evaluation/reports/<id>.md`) reports.

## Baseline result

The checked-in baseline was measured by running the baseline configuration. Its source of truth is `evaluation/reports/baseline.json`.

| Field | Value |
| --- | --- |
| Dataset | `ragbench-v2-baseline` |
| Dataset version | `1.0.0` |
| Questions | 10 |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Chunk size | 800 characters |
| Chunk overlap | 100 characters |
| Store and distance | In-memory Qdrant, cosine |
| Retrieval depth | 5 chunks |
| Recall@1 | 0.900000 |
| Recall@3 | 0.900000 |
| Recall@5 | 1.000000 |
| MRR | 0.925000 |

Question `q007` retrieved the relevant `generation` document at rank 4. That question scored zero for Recall@1 and Recall@3, one for Recall@5, and 0.25 reciprocal rank. All relevant documents were present within the configured top-5 depth, so the baseline top-k failure list is empty.

These values describe only this small authored dataset. They are not evidence of performance on other corpora or question distributions.

## Result schema

The JSON artifact includes:
- schema and experiment identifiers (`schema_version: "3"`);
- UTC timestamp;
- dataset name, version, and content fingerprint;
- logical-to-content-derived corpus document mapping;
- chunk, embedding, Qdrant, and top-k configuration;
- relevant software versions;
- aggregate metrics;
- per-query retrieved documents, chunks, scores, and metrics;
- top-k missed-document records;
- latency statistics (`timing.embedding_latency`, `timing.retrieval_latency`, percentiles);
- hypothesis and changed parameter description; and
- neutral interpretation and decision.

## Regression comparison

Compare two result files with:

```bash
python -m ragbench.experiments compare evaluation/reports/baseline.json evaluation/reports/chunk-400-50.json
```

For every metric and latency measurement, the comparison computes `experiment - baseline`. Comparison rejects different dataset versions, dataset fingerprints, query counts, or metric sets.

## Generation evaluation

Generation evaluation is implemented in `evaluation/generation_evaluator.py` and executed via `evaluation/generation_runner.py`:

```bash
python -m ragbench.eval_generation
```

The evaluator assesses three distinct dimensions on a [0.0, 1.0] scale without creating an arbitrary composite single score:

### 1. Correctness

Measures whether factual requirements of the reference answer are satisfied in the generated answer:

\[
\text{Correctness} = \frac{\text{count of satisfied required facts}}{\text{total required facts}}
\]

A fact is satisfied if it appears in the normalized generated text or has \(\ge 80\%\) content token containment. If `required_facts` is absent, normalized content token overlap with `reference_answer` is computed.

### 2. Faithfulness / Groundedness

Measures whether statements made in the generated answer are supported by the retrieved context:

\[
\text{Faithfulness} = \frac{\text{count of supported claims}}{\text{total claims in answer}}
\]

Generated text is split into distinct sentence claims. A claim is supported if its content tokens have \(\ge 70\%\) containment in the retrieved context. When context is empty, an explicit statement acknowledging insufficient context is treated as faithful.

### 3. Context Relevance

Measures whether evidence retrieved into context contains the target relevant documents:

\[
\text{Context Relevance} = 0.5 \times \mathbb{I}(\text{rank}_1 \in R_q) + 0.5 \times \frac{|\{c \in \text{retrieved chunks} : \text{doc}(c) \in R_q\}|}{|\text{retrieved chunks}|}
\]

This rewards both top-1 precision and evidence density while penalizing irrelevant noise in the context window.

### Decoupled LLM-as-a-Judge

`LLMJudgeGenerationEvaluator` provides an optional evaluator that prompts an LLM with structured JSON output instructions (`correctness`, `faithfulness`, `context_relevance`, `reason`). The judge response is schema-validated, clamped to [0.0, 1.0], and logs `judge_model`, `judge_prompt_version`, and `judge_temperature`. Model-based judgments are not treated as objective ground truth.

## V5 Regression Detection and CI Quality Gate

The regression detection engine (`ragbench.regression.engine`) answers:
> *When a RAG system changes, did quality improve without unacceptable latency, cost, or reliability regressions?*

### Multi-Dimensional Evaluation Dimensions

1. **Retrieval Quality**: Recall@1, Recall@3, Recall@5, MRR minimum allowable deltas.
2. **Generation Quality**: Answer correctness, faithfulness, context relevance minimum deltas.
3. **Latency**: P95 retrieval and end-to-end relative increase caps (e.g. max +25%).
4. **Cost**: Cost per query relative increase caps (e.g. max +30%).
5. **Reliability**: Maximum allowable failure rate (e.g. 5%) and zero-timeout requirement.

### Tri-State Decision Output

- **`pass`**: All evaluated metrics satisfy configured thresholds.
- **`fail`**: One or more metrics violated allowable regression thresholds.
- **`inconclusive`**: Required measurements are missing (e.g. unconfigured pricing) or dataset versions mismatch (`1.0.0` vs `1.1.0`). Missing data is never silently treated as success.

### CI Quality Gate Integration

A dedicated GitHub Actions job (`regression-gate` in `.github/workflows/ci.yml`) executes the deterministic benchmark against versioned dataset `1.1.0` and gates merges:
- Runs offline without requiring paid external LLM API credentials
- Emits structured JSON (`regression_decision.json`) and Markdown inspection summaries
- Exits with standard status codes (0 for pass, 1 for fail, 2 for inconclusive)

## Test Coverage

The test suite contains **150 passing tests** covering:
- dataset validation, malformed records, and unknown documents;
- Recall@K and MRR formulas and boundary cases;
- empty retrieval and duplicate retrieved IDs;
- typed experiment configuration and single-variable enforcement;
- latency percentile aggregation (p50, p95, p99);
- comparison metric, latency, cost, and reliability signed deltas;
- deterministic correctness, faithfulness, and context relevance;
- decoupled LLM judge parsing, clamping, and timeout recovery;
- provider-neutral cost accounting, token normalization, and pricing lookup;
- regression detection pass, fail, inconclusive, and boundary conditions;
- safe bounded retries (transient 5xx, rate limits, timeouts) vs non-retryable 4xx errors;
- structured request observation models and recursive secret/token redaction;
- controlled concurrency benchmarks across concurrency levels 1, 2, 5;
- controlled recovery tests (vector store down, embedding failure, malformed responses); and
- health liveness (`/health`) and readiness (`/ready`) endpoints.
