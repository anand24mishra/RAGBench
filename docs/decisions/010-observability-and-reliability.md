# ADR-010: Request Tracing, Secret Sanitization, and Safe Retries

Status: Accepted for V5 observability, security, and reliability

## Context

Production RAG systems require structured request tracing across embedding, retrieval, context formatting, and LLM generation. At the same time, naive logging frequently exposes sensitive credentials (API keys, Authorization headers) or leaks complete document content. Furthermore, unbounded or blind retries against external LLM providers can cause retry amplification and cascade failures.

## Options Considered

- **Ad-hoc Logging and Blanket Retries**: Log raw request/response payloads and retry all exceptions indiscriminately.
- **Distributed OpenTelemetry Integration**: Introduce heavy external distributed tracing collectors.
- **Structured Correlation Tracing with Bounded Safe Retries and Redaction**: Propagate correlation IDs (`request_id`, `experiment_id`, `query_id`), redact sensitive fields in logging formatters, separate internal observability telemetry from public API schemas, and enforce bounded retries on transient errors only.

## Decision

1. **Structured Telemetry**:
   - Propagate `request_id` throughout all pipeline stages (`request -> embedding -> retrieval -> context -> generation -> response`).
   - Define typed `RequestObservation` encapsulating retrieval, generation, timing, and error details, keeping instrumentation separate from public API response models.
2. **Security & Sanitization**:
   - Sanitize all log payloads in `JsonFormatter`, redacting authorization headers, API keys, tokens, and credentials with `[REDACTED]`.
   - Never log authorization headers or full document payloads unnecessarily.
3. **Health & Readiness Separation**:
   - `GET /health`: Liveness probe (checks process execution only, avoids expensive dependency probes).
   - `GET /ready`: Readiness probe (checks that internal pipeline services, embedding models, and vector stores are initialized).
4. **Safe Bounded Retries**:
   - Retries only safe, transient failures: HTTP 429 (rate limits), HTTP 5xx (transient gateway/server errors), and network timeouts.
   - Strictly prohibit retrying deterministic client errors (HTTP 4xx, bad requests, validation errors, malformed responses).
   - Enforce bounded exponential backoff with max attempts (default 3) and max delay caps.

## Reasoning

Separating liveness from readiness prevents cascading restarts in container orchestrators like Kubernetes. Bounded, status-code-aware retries prevent retry storms while absorbing transient network blips. Automatic redaction ensures credential safety.

## Trade-offs

Readiness probes check local service readiness; distributed external Qdrant clusters or remote LLMs are not pinged on every health check to prevent DDoS and latency degradation.

## Consequences

FastAPI routes, pipeline execution, and providers emit consistent JSON logs with correlation IDs and bounded retry behavior. Controlled failure and recovery tests verify resilience.
