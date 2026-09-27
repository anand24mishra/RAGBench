# RAG Pipeline

## Status

The V1 ingestion, indexing, retrieval, context, and generation path is implemented. V2 evaluates document retrieval with Recall@1/3/5 and MRR. V3 adds typed controlled retrieval experiments and stage-level latency benchmarking without changing this core production pipeline. V4 evaluates generation quality (correctness, faithfulness, context relevance) with deterministic scoring and optional decoupled LLM judging. Hybrid search, metadata filtering, and reranking remain planned.

## Ingestion

Supported formats are UTF-8 plain text (`.txt`) and Markdown (`.md` or `.markdown`). Uploads arrive as multipart data on `POST /ingest`; the default limit is 2,000,000 bytes.

The loader decodes the original bytes as UTF-8, rejects whitespace-only content, and creates the document ID as the lowercase SHA-256 digest of those bytes. Re-uploading byte-identical content produces the same document ID. Metadata is limited to:

- `source`, currently `upload` through the API;
- `filename`, stripped to its base name; and
- `document_id`.

Markdown is treated as text. V1 does not parse headings, links, code blocks, front matter, or tables into a structural representation.

## Chunking

The implemented strategy is fixed-size character chunking:

- default `CHUNK_SIZE`: 800 characters;
- default `CHUNK_OVERLAP`: 100 characters;
- next start offset: `chunk_size - chunk_overlap`.

Both values are validated, and overlap must be smaller than chunk size. The final chunk may be shorter. No whitespace or sentence-boundary adjustment is applied.

Each chunk contains its text, source document ID, inherited metadata, zero-based chunk index, and character offsets. Its ID is a SHA-256 digest of document ID, start offset, and end offset. This gives stable IDs for an unchanged document and chunk configuration.

In V3 experiments, alternative chunk configurations (e.g. 400/50 and 1200/150) were evaluated against the 800/100 baseline. Finer 400-character chunks elevated relevant passage ranking for `q007` while increasing total chunk count.

## Embeddings

The implementation uses `sentence-transformers`. The model is configured by `EMBEDDING_MODEL`; the default is `sentence-transformers/all-MiniLM-L6-v2`. Its commonly reported dimension is 384, but the code does not hard-code that value. It asks the loaded model for its dimension and uses that value when creating or validating the Qdrant collection.

Documents are embedded in batches controlled by `EMBEDDING_BATCH_SIZE`, default 32. Queries and documents use the same model and code path. `normalize_embeddings=True` is passed to the library. Empty batches return an empty list; blank individual texts and queries are rejected.

In V3, the model is fully configurable. An alternative 3-layer model (`sentence-transformers/paraphrase-MiniLM-L3-v2`, 384 dimensions) was benchmarked and evaluated, demonstrating a ~52% reduction in steady-state query embedding latency (3.45 ms vs. 7.22 ms) while retaining target evidence recall.

## Vector storage

Qdrant is the implemented vector store. The development stack pins the Qdrant container to `v1.15.4`; the Python client is constrained to major version 1.

The adapter creates one cosine-distance collection using the model-reported dimension. Upserts contain the vector plus chunk ID, document ID, text, and metadata. Search reconstructs typed retrieved chunks and retains Qdrant scores. A pre-existing collection with a different unnamed-vector dimension is rejected rather than silently reused.

V1 does not delete old chunks when the contents at a filename change, and it does not expose document deletion. In evaluation and benchmarking, each run utilizes an isolated in-memory collection to prevent cross-experiment contamination.

## Retrieval

`SemanticRetriever` performs dense top-k search:

1. validate and embed the query;
2. query the configured Qdrant collection using cosine similarity;
3. preserve Qdrant result order; and
4. return text, chunk ID, document ID, score, and metadata.

`TOP_K` defaults to 5. A request can override it from 1 through 100. There is no score threshold, metadata filter, lexical retrieval, or query rewriting.

V3 experiments tested `top_k` values 1, 3, 5, and 10. Retrieval depths below 4 (`topk-1` and `topk-3`) omitted evidence for query `q007`, demonstrating the necessity of at least top-5 depth on this dataset.

## Reranking

Not implemented. Reranking should be evaluated only after a relevance dataset shows that useful chunks enter the candidate set but are ranked below the context cutoff.

## Context construction

Retrieved chunks are formatted in retrieval order. Each section includes a one-based source label, filename, document ID, chunk ID, and content. Sections are separated by blank lines.

`CONTEXT_CHAR_LIMIT`, default 12,000, is a hard character limit. Whole later sections are omitted when they do not fit. If the first section alone exceeds the limit, its formatted representation is truncated. The response includes only chunks admitted by the context builder, although the returned source text is the complete chunk text. Token-aware budgeting and duplicate suppression are not implemented.

## Generation

The provider abstraction exposes one asynchronous `generate` operation. V1 implements an OpenAI-compatible chat-completions adapter configured by:

- `LLM_PROVIDER`, currently only `openai`;
- `LLM_MODEL`, default `gpt-4o-mini`;
- `LLM_API_KEY`, required at startup;
- `LLM_BASE_URL`, default `https://api.openai.com/v1`;
- `LLM_TIMEOUT_SECONDS`, default 30;
- `LLM_TEMPERATURE`, default 0; and
- `LLM_MAX_TOKENS`, default 500.

The system prompt directs the model to use only supplied context, report insufficient information, avoid treating retrieved instructions as system instructions, and state uncertainty. This reduces ambiguity in expected behavior but does not guarantee that hallucinations are prevented.

The adapter returns the provider's model identifier and prompt/completion token counts when supplied. A live provider response has not been evaluated for quality.

## Timing

The query response reports four monotonic-clock measurements:

- `embedding_ms` for query embedding;
- `retrieval_ms` for Qdrant search after the vector is available;
- `generation_ms` for the provider request, or zero when generation is skipped; and
- `total_ms` for pipeline orchestration from retrieval start through response construction.

V3 introduces aggregate benchmarking (`benchmarks/runner.py` and `benchmarks/timing.py`) that separates model initialization from steady-state query latencies and computes mean, p50, p95, and p99 distributions.
