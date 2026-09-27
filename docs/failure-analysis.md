# Failure Analysis

## Status

V1 deliberately tests boundary failures using deterministic fixtures. V2 adds per-query retrieval measurements and records one observed ranking weakness in the baseline. V3 adds automated rank movement tracking and captures failures under shallow retrieval depths. Generation-quality failures remain unevaluated.

## FA-001: No retrieval results

**Failure:** A query returns no chunks.

**Observed behavior:** The pipeline returns `The available context is insufficient to answer this question.`, an empty source list, zero generation time, and no LLM call.

**Reproduction:** `tests/unit/test_pipeline.py::test_pipeline_does_not_call_llm_without_retrieval_results` uses an empty vector store.

**Root cause:** No points are available for the semantic search.

**Impact:** The request cannot be answered from indexed evidence.

**Fix:** This is treated as an explicit grounded outcome rather than an internal error or an ungrounded generation attempt.

**Regression test:** The test asserts the refusal text, empty sources, zero generation time, and zero provider calls.

## FA-002: Malformed provider output

**Failure:** The provider returns a successful HTTP response without the expected answer structure.

**Observed behavior:** The adapter raises `LLMProviderError` with the safe message `LLM provider returned an invalid response`.

**Reproduction:** `tests/unit/test_provider.py::test_provider_rejects_malformed_response` returns an empty JSON object through `httpx.MockTransport`.

**Root cause:** Required `choices[0].message.content` data is absent.

**Impact:** No answer is returned; the API maps the provider error to HTTP 502.

**Fix:** Validate response shape before constructing a generation result and classify invalid data separately from timeouts.

**Regression test:** The provider unit test asserts the typed exception and message.

## FA-003: Invalid document input

**Failure:** Empty, non-UTF-8, or unsupported file content is submitted.

**Observed behavior:** The loader rejects the document before chunking or embedding. API tests verify HTTP 400 for an unsupported extension.

**Reproduction:** Loader tests cover whitespace-only bytes, invalid UTF-8, and `.pdf`, missing, and `.json` suffixes.

**Root cause:** Input violates V1's plain-text and Markdown contract.

**Impact:** No chunk or vector is written.

**Fix:** Validate extension, decoding, and non-whitespace content at the loader boundary.

**Regression test:** `tests/unit/test_loader.py` and `tests/integration/test_api.py::test_invalid_document_returns_explicit_error`.

## FA-004: Relevant generation document ranked fourth in baseline

**Failure:** The relevant document for `q007`, "What does the pipeline do when retrieval returns no chunks?", was not present in the first three unique document results under baseline configuration.

**Observed behavior:** Retrieval order in baseline was `chunking`, `retrieval`, `observability`, `generation`, `ingestion`. The query received Recall@1 of 0, Recall@3 of 0, Recall@5 of 1, and reciprocal rank of 0.25.

**Reproduction:** Run `python -m ragbench.eval` with `experiments/baseline/config.yaml`. Inspect `q007` in `evaluation/reports/baseline.json`.

**Root cause:** Query phrasing combines retrieval and generation concepts, while evidence is located in the generation document. Baseline 800-character chunks placed adjacent documents ahead of target evidence.

**V3 Experimental Findings:**
- In `chunk-400-50` (400-character chunks), `generation` moved from **rank 4 to rank 1** (score 0.2912 -> 0.5402), raising Recall@3 to 1.0 and MRR to 0.9500.
- In `embed-paraphrase-minilm-l3-v2`, `generation` also moved from **rank 4 to rank 1** (score 0.2912 -> 0.4285).
- In `chunk-1200-150` (1200-character chunks), `generation` remained at **rank 4**.

## FA-005: Evidence omission under shallow retrieval (top_k < 4)

**Failure:** Under `top_k=1` and `top_k=3`, query `q007` completely fails to retrieve target evidence.

**Observed behavior:**
- Under `topk-1`: only 1 candidate (`chunking`) is retrieved; `generation` is absent. Recall@1=0, Recall@3=0, Recall@5=0, MRR=0.
- Under `topk-3`: 3 candidates (`chunking`, `retrieval`, `observability`) are retrieved; `generation` is absent. Recall@1=0, Recall@3=0, Recall@5=0, MRR=0.

**Reproduction:** Run `python -m ragbench.experiments run experiments/top_k/k1.yaml` or `experiments/top_k/k3.yaml`. Inspect failure records in `evaluation/reports/topk-1.json` and `evaluation/reports/topk-3.json`.

**Root cause:** Target evidence was ranked 4th. Configuring retrieval depth below the true target rank truncates candidates before evaluation.

**Fix:** Maintain retrieval depth of at least `top_k=5` for this workload to prevent recall dropouts.

## V4 Generation Quality Failure Taxonomy

RAGBench V4 introduces a multi-stage typed failure taxonomy classifying failures by the pipeline stage responsible:

| Failure Type | Definition | Stage |
| --- | --- | --- |
| `retrieval_failure` | Target relevant document was absent from all top-k candidates | Retrieval |
| `context_failure` | Context relevance is below 0.25 (target document missing or overwhelmed by non-target noise) | Context construction |
| `generation_failure` | Retrieved context was relevant, but generated answer missed required facts (correctness < 0.70) | Generation |
| `grounding_failure` | Generated answer asserted claims unsupported by retrieved context (faithfulness < 0.70) | Generation / Grounding |
| `provider_failure` | Generation provider or judge timed out, crashed, or returned malformed structure | Provider boundary |

### Distinguishing Retrieval Failure from Generation Failure

A fundamental failure mode in RAG systems is confusing **retrieval failure** (the right document was never retrieved) with **generation failure** (the right document was in context, but the LLM hallucinated or failed to answer). V4 explicitly differentiates these:
- If `retrieved_documents` contains no relevant document: classified as `retrieval_failure`.
- If `retrieved_documents` contains the document, but `faithfulness < 0.70`: classified as `grounding_failure`.
- If `retrieved_documents` contains the document and claims are grounded, but reference facts are omitted: classified as `generation_failure`.

## Quality failure matrix

| Scenario | Required evidence | Status |
| --- | --- | --- |
| Irrelevant retrieval | Known-relevant document absent from configured top-k | Implemented (`retrieval_failure`) |
| Context noise / truncation | Low target evidence density in context window | Implemented (`context_failure`) |
| Hallucinated answer | Claim tokens unsupported by retrieved context | Implemented (`grounding_failure`) |
| Missing answer facts | Grounded answer missing required reference facts | Implemented (`generation_failure`) |
| Provider failure | LLM provider timeout, error, or malformed JSON | Implemented (`provider_failure`) |
| Contradictory documents | Versioned conflicting-source fixture and answer rubric | Planned |
| Duplicate chunks | Duplicate corpus fixture and diversity measurement | Planned |
| Retrieval timeout | Network fault injection against Qdrant | Planned |

Suspected causes should remain hypotheses until a controlled reproduction and observable evidence identify the failing stage.
