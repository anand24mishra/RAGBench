# Generation Quality Evaluation: `generation-v4-baseline`

- **Date:** 2026-09-27 00:11:47 UTC
- **Dataset:** `ragbench-v4-generation` version `1.1.0`
- **Dataset Fingerprint:** `255edea5ef99c742a1d9a6ddeeb04d1174815658ee35825d2d2881d9d52fd49d`
- **Corpus Fingerprint:** `369f2ec2725cdeefa7d9baae244d1158c7ef8b2bae17f12c034b85364ac90898`
- **Corpus Scope:** 5 documents, 28 questions
- **Evaluator Type:** `deterministic`
- **Generation Model:** `grounded-deterministic`
- **Judge Model:** `None (deterministic evaluation)`

## Retrieval Quality Metrics

| Metric | Result |
| --- | ---: |
| Recall@1 | 0.857143 |
| Recall@3 | 0.964286 |
| Recall@5 | 1.000000 |
| MRR | 0.907738 |

## Generation Quality Metrics

| Metric | Result | Description |
| --- | ---: | --- |
| Correctness | 0.744048 | Proportion of grounded reference facts satisfied in generated answer |
| Faithfulness | 1.000000 | Proportion of generated answer claims directly supported by retrieved context |
| Context Relevance | 0.528571 | Proportion of relevant target documents retrieved into context |

## Cost & Token Accounting

- **Cost Status:** `unavailable` (model pricing not configured)

## Reliability & Failure Accounting

- **Total Requests:** 28
- **Successful Requests:** 15
- **Failed Requests:** 13
- **Failure Rate:** 46.43%
- **Timeouts:** 0
- **Provider Errors:** 0
- **Failure Categories:** generation_failure: 9, context_failure: 4

## Performance & Latency Measurements

- **Sample size:** 28 queries
- **Total evaluation runtime:** 585.09 ms

| Phase | Mean (ms) | p50 (ms) | p95 (ms) | p99 (ms) |
| --- | ---: | ---: | ---: | ---: |
| Query Embedding | 12.307 | 8.381 | 26.001 | 27.056 |
| Vector Retrieval | 0.699 | 0.371 | 0.688 | 6.637 |
| Generation | 0.283 | 0.265 | 0.316 | 0.542 |

## Failure Analysis & Classification

Observed **13** generation failure(s):

| Query ID | Failure Type | Expected Evidence | Failed Metric | Reason |
| --- | --- | --- | --- | --- |
| `q001` | `generation_failure` | ingestion | generation_failure | Correctness 0.67 below threshold 0.70; missing required facts: ['.txt, .md, or .markdown'] |
| `q003` | `generation_failure` | chunking | generation_failure | Correctness 0.50 below threshold 0.70; missing required facts: ['800-character chunks'] |
| `q004` | `generation_failure` | chunking | generation_failure | Correctness 0.67 below threshold 0.70; missing required facts: ['start and end character offsets'] |
| `q005` | `generation_failure` | retrieval | generation_failure | Correctness 0.00 below threshold 0.70; missing required facts: ['Qdrant', 'cosine distance'] |
| `q006` | `generation_failure` | retrieval | generation_failure | Correctness 0.00 below threshold 0.70; missing required facts: ['dense top-k retrieval', 'without hybrid search or reranking'] |
| `q007` | `context_failure` | generation | context_failure | Context relevance 0.10 below threshold 0.25 |
| `q009` | `generation_failure` | observability | generation_failure | Correctness 0.50 below threshold 0.70; missing required facts: ['omit document bodies', 'queries'] |
| `q011` | `generation_failure` | ingestion | generation_failure | Correctness 0.00 below threshold 0.70; missing required facts: ['unsupported extensions', 'invalid UTF-8', 'whitespace'] |
| `q017` | `generation_failure` | retrieval | generation_failure | Correctness 0.00 below threshold 0.70; missing required facts: ['same configured sentence-transformer model', 'embeddings are normalized'] |
| `q018` | `context_failure` | retrieval | context_failure | Context relevance 0.10 below threshold 0.25 |
| `q020` | `context_failure` | retrieval | context_failure | Context relevance 0.10 below threshold 0.25 |
| `q021` | `generation_failure` | generation | generation_failure | Correctness 0.00 below threshold 0.70; missing required facts: ['model', 'base URL', 'timeout', 'temperature', 'maximum output tokens'] |
| `q024` | `context_failure` | generation | context_failure | Context relevance 0.10 below threshold 0.25 |


## Per-Query Inspection

### Query `q001`: *Which file formats does RAGBench V1 accept for ingestion?*

- **Status:** `generation_failure`
- **Expected Document:** ingestion
- **Retrieved Top Documents:** ingestion, retrieval, chunking
- **Generated Answer:** "RAGBench V1 uses dense semantic retrieval. RAGBench V1 accepts UTF-8 plain-text and Markdown documents. The V1 baseline uses fixed-size character chunks."
- **Reference Answer:** "RAGBench V1 accepts UTF-8 plain-text files and Markdown files with .txt, .md, or .markdown extensions."
- **Metrics:** Correctness: 0.67, Faithfulness: 1.00, Context Relevance: 0.60

### Query `q003`: *What chunk size and overlap does the baseline use?*

- **Status:** `generation_failure`
- **Expected Document:** chunking
- **Retrieved Top Documents:** chunking, retrieval, ingestion
- **Generated Answer:** "The default chunk size is 800 characters and the default overlap is 100 characters. The next chunk begins at `chunk_size - chunk_overlap`. The V1 baseline uses fixed-size character chunks."
- **Reference Answer:** "The baseline uses 800-character chunks with 100 characters of overlap."
- **Metrics:** Correctness: 0.50, Faithfulness: 1.00, Context Relevance: 0.60

### Query `q004`: *How are chunk identifiers made deterministic?*

- **Status:** `generation_failure`
- **Expected Document:** chunking
- **Retrieved Top Documents:** chunking, ingestion, retrieval
- **Generated Answer:** "The chunk ID is a SHA-256 digest derived from the document ID and those start and end offsets, making the result deterministic for unchanged content and configuration. The next chunk begins at `chunk_size - chunk_overlap`. Each chunk preserves the source document ID and metadata."
- **Reference Answer:** "A chunk ID is derived from the document ID and the chunk's start and end character offsets."
- **Metrics:** Correctness: 0.67, Faithfulness: 1.00, Context Relevance: 0.60

### Query `q005`: *Which vector database and distance function are used for semantic retrieval?*

- **Status:** `generation_failure`
- **Expected Document:** retrieval
- **Retrieved Top Documents:** retrieval, observability, chunking
- **Generated Answer:** "RAGBench V1 uses dense semantic retrieval. Structured JSON events cover request completion, retrieval, generation, and handled failures. If retrieval returns no chunks, the pipeline returns an insufficient-context answer without calling the LLM provider."
- **Reference Answer:** "RAGBench uses Qdrant with cosine distance."
- **Metrics:** Correctness: 0.00, Faithfulness: 1.00, Context Relevance: 0.60

### Query `q006`: *Does the V1 retriever use hybrid search or reranking?*

- **Status:** `generation_failure`
- **Expected Document:** retrieval
- **Retrieved Top Documents:** retrieval, observability, chunking
- **Generated Answer:** "V1 does not implement lexical search, hybrid retrieval, metadata filtering, a score threshold, or reranking. RAGBench V1 uses dense semantic retrieval. The V1 baseline uses fixed-size character chunks."
- **Reference Answer:** "No. V1 uses dense top-k retrieval without hybrid search or reranking."
- **Metrics:** Correctness: 0.00, Faithfulness: 1.00, Context Relevance: 0.60

### Query `q007`: *What does the pipeline do when retrieval returns no chunks?*

- **Status:** `context_failure`
- **Expected Document:** generation
- **Retrieved Top Documents:** chunking, retrieval, observability
- **Generated Answer:** "If retrieval returns no chunks, the pipeline returns an insufficient-context answer without calling the LLM provider. The retriever returns the top-k chunks in Qdrant rank order with chunk ID, document ID, text, metadata, and similarity score. The V1 baseline uses fixed-size character chunks."
- **Reference Answer:** "It returns an insufficient-context answer and does not call the LLM provider."
- **Metrics:** Correctness: 0.50, Faithfulness: 1.00, Context Relevance: 0.10

### Query `q009`: *Does application logging include full uploaded documents and user questions?*

- **Status:** `generation_failure`
- **Expected Document:** observability
- **Retrieved Top Documents:** observability, ingestion, chunking
- **Generated Answer:** "Application logging omits uploaded document bodies, user questions, retrieved text, generated answers, API keys, and authorization headers. RAGBench V1 accepts UTF-8 plain-text and Markdown documents. The document ID is the SHA-256 digest of the original uploaded bytes."
- **Reference Answer:** "No. Application logs omit document bodies, queries, retrieved text, and generated answers."
- **Metrics:** Correctness: 0.50, Faithfulness: 1.00, Context Relevance: 0.60

### Query `q011`: *What conditions cause the document loader to reject an uploaded file during ingestion?*

- **Status:** `generation_failure`
- **Expected Document:** ingestion
- **Retrieved Top Documents:** ingestion, chunking, observability
- **Generated Answer:** "The document ID is the SHA-256 digest of the original uploaded bytes. Application logging omits uploaded document bodies, user questions, retrieved text, generated answers, API keys, and authorization headers. Each chunk preserves the source document ID and metadata."
- **Reference Answer:** "The loader rejects unsupported extensions, invalid UTF-8, and content containing only whitespace."
- **Metrics:** Correctness: 0.00, Faithfulness: 1.00, Context Relevance: 0.60

### Query `q017`: *How are document and query embeddings generated in RAGBench V1 retrieval?*

- **Status:** `generation_failure`
- **Expected Document:** retrieval
- **Retrieved Top Documents:** retrieval, ingestion, chunking
- **Generated Answer:** "RAGBench V1 uses dense semantic retrieval. RAGBench V1 accepts UTF-8 plain-text and Markdown documents. V1 does not implement lexical search, hybrid retrieval, metadata filtering, a score threshold, or reranking."
- **Reference Answer:** "The same configured sentence-transformer model embeds both documents and queries, and embeddings are normalized."
- **Metrics:** Correctness: 0.00, Faithfulness: 1.00, Context Relevance: 0.60

### Query `q018`: *What information is returned for each chunk in the retriever output?*

- **Status:** `context_failure`
- **Expected Document:** retrieval
- **Retrieved Top Documents:** chunking, observability, retrieval
- **Generated Answer:** "The retriever returns the top-k chunks in Qdrant rank order with chunk ID, document ID, text, metadata, and similarity score. The next chunk begins at `chunk_size - chunk_overlap`. Each chunk preserves the source document ID and metadata."
- **Reference Answer:** "The retriever returns the chunk ID, document ID, text, metadata, and similarity score in Qdrant rank order."
- **Metrics:** Correctness: 1.00, Faithfulness: 1.00, Context Relevance: 0.10

### Query `q020`: *What is the default top-k retrieval depth in the V1 baseline?*

- **Status:** `context_failure`
- **Expected Document:** retrieval
- **Retrieved Top Documents:** chunking, retrieval, observability
- **Generated Answer:** "The default top-k is 5. The V1 baseline uses fixed-size character chunks. RAGBench V1 uses dense semantic retrieval."
- **Reference Answer:** "The default top-k retrieval depth is 5 chunks."
- **Metrics:** Correctness: 1.00, Faithfulness: 1.00, Context Relevance: 0.10

### Query `q021`: *What parameters are configurable for the generation LLM provider?*

- **Status:** `generation_failure`
- **Expected Document:** generation
- **Retrieved Top Documents:** generation, observability, chunking
- **Generated Answer:** "Generation uses an asynchronous OpenAI-compatible provider selected through typed configuration. If retrieval returns no chunks, the pipeline returns an insufficient-context answer without calling the LLM provider. The API enforces a configurable upload-size limit before chunking and embedding."
- **Reference Answer:** "Model, base URL, timeout, temperature, and maximum output tokens are configurable."
- **Metrics:** Correctness: 0.00, Faithfulness: 1.00, Context Relevance: 0.60

### Query `q024`: *What type of LLM provider does RAGBench generation use?*

- **Status:** `context_failure`
- **Expected Document:** generation
- **Retrieved Top Documents:** ingestion, retrieval, generation
- **Generated Answer:** "Generation uses an asynchronous OpenAI-compatible provider selected through typed configuration. If retrieval returns no chunks, the pipeline returns an insufficient-context answer without calling the LLM provider. RAGBench V1 uses dense semantic retrieval."
- **Reference Answer:** "Generation uses an asynchronous OpenAI-compatible provider selected through typed configuration."
- **Metrics:** Correctness: 1.00, Faithfulness: 1.00, Context Relevance: 0.10

