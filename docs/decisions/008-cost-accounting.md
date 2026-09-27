# ADR-008: Provider-Neutral Cost Accounting and Pricing Registry

Status: Accepted for V5 production evaluation and cost analysis

## Context

Evaluating RAG systems solely on retrieval or generation quality ignores operational expenditure. Different models, chunk sizes, and retrieval depths directly influence input and output token consumption. Hardcoding pricing into model provider code couples infrastructure to volatile commercial pricing tables and prevents retrospective analysis.

## Options Considered

- **Hardcoded Pricing in LLM Providers**: Embed pricing directly into OpenAI or Anthropic provider implementations.
- **Dynamic Live Pricing APIs**: Query commercial pricing APIs at runtime.
- **Provider-Neutral Pricing Registry with Configurable YAML**: Maintain an explicit, provider-neutral pricing table with effective dates, calculating query and aggregated costs while explicitly preserving `cost_status: unavailable` when pricing is missing.

## Decision

1. Create `PricingRegistry` loaded from `data/pricing.yaml` mapping models to per-1M token pricing in USD.
2. Record normalized token usage (`input_tokens`, `output_tokens`, `total_tokens`) and costs (`input_cost`, `output_cost`, `total_cost`, `cost_per_query`) on every query.
3. If pricing or token counts are unavailable, mark `cost_status: unavailable` and keep cost values `None` rather than fabricating numbers.
4. Support model aliases and prefix matching (e.g. `gpt-4o-mini-2024-07-18` matching `gpt-4o-mini`).

## Reasoning

A decoupled pricing registry keeps provider implementations clean and allows reproducible evaluations across different pricing regimes or self-hosted models where inference cost is zero or amortized. Explicit unavailable states prevent false precision and random estimations.

## Trade-offs

Token counts reported by mock providers or synthetic responses approximate real tokenizer counts. When using commercial models, provider-reported usage is utilized.

## Consequences

Experiment and evaluation artifacts record cost accounting metrics. Regressions in cost per query can be caught automatically during CI/CD evaluation gates.
