# ADR-007: Deterministic Generation Evaluation and Decoupled LLM-as-a-Judge

Status: Accepted for V4 generation evaluation

## Context

Retrieval evaluation verifies that relevant documents or passages are returned, but does not guarantee that the generated answer is correct, faithful to retrieved evidence, or directly answers the user's question. Evaluating generated answers exclusively via LLM-as-a-judge introduces non-determinism, API cost, hidden prompt bias, and makes automated testing brittle.

## Options Considered

- **LLM Judge as Sole Truth**: Use a large language model to rate answer quality without deterministic validation.
- **Pure Exact String Matching**: Match generated text against reference answers via exact substring or BLEU/ROUGE.
- **Deterministic Grounded Evaluator with Optional LLM Judge**: Use manually authored, corpus-grounded facts for deterministic correctness, sentence-to-context containment for faithfulness, and decouple LLM judging behind a pluggable interface.

## Decision

1. Implement `DeterministicGenerationEvaluator` as the primary, reproducible baseline evaluator.
2. Measure three distinct generation dimensions:
   - **Correctness**: Ratio of required reference facts satisfied in the generated answer via normalized entity/token coverage.
   - **Faithfulness / Groundedness**: Ratio of claims in the generated answer supported by retrieved context tokens, identifying hallucinations.
   - **Context Relevance**: Ratio and rank of relevant target documents present in retrieved context.
3. Decouple `LLMJudgeGenerationEvaluator` behind `GenerationEvaluator`, requesting structured JSON ratings and recording model configuration, temperature, and prompt version without treating judge output as ground truth.
4. Classify failures systematically into `retrieval_failure`, `context_failure`, `grounding_failure`, `generation_failure`, and `provider_failure`.

## Why

A deterministic-first evaluator runs locally without external API dependencies, operates deterministically in CI, and provides explainable, reproducible scoring for benchmark datasets. Decoupling the LLM judge allows teams to compare deterministic rule-based checks with model-based judgments when credentials and compute are available.

## Trade-offs

Deterministic fact matching requires human curation of `required_facts` and `reference_answer`. It can miss semantic paraphrases that use completely disjoint vocabulary. Pluggable LLM judging addresses phrasing flexibility when enabled.

## Consequences

The evaluation dataset is incremented to version `1.1.0` (28 grounded questions across 5 corpus documents). Evaluation results record `generation_evaluation` metrics, stage latencies (embedding, retrieval, generation), and per-query failure inspections in both JSON and Markdown artifacts.
