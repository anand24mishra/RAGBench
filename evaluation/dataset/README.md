# Retrieval Dataset 1.0.0

This dataset is a small, repository-specific retrieval baseline. It is not intended to represent general RAG workloads.

## Contents

- `corpus/` contains five Markdown documents describing verified RAGBench behavior.
- `questions.jsonl` contains ten questions with stable IDs, relevant logical document IDs, and reference answers.
- `metadata.json` defines the dataset name, version, and allowed logical document IDs.

## Creation method

The corpus was divided by engineering responsibility: ingestion, chunking, retrieval, generation, and observability. Questions were written manually after the corpus. A document was marked relevant only when it directly contains the evidence required to answer the question. Reference answers paraphrase explicit corpus statements and are not used by the V2 retrieval evaluator.

The current labels were created by the implementation author and have not received independent annotation. Each question currently has one relevant document. This makes the baseline inspectable but does not test multi-document recall or ambiguous relevance.

## Versioning rules

Changing document text, questions, reference answers, or relevance labels requires a dataset-version change. The runner records a SHA-256 fingerprint over metadata, questions, and corpus content. Result comparison rejects artifacts with different fingerprints even if their declared version strings match.

Document IDs are filename stems. The runner maps them to the content-derived IDs created by the production loader and records that mapping in the result artifact.
