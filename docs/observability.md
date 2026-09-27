# Observability

## Status

Structured JSON application logs, stage-level latency instrumentation, request correlation IDs, typed observation models (`RequestObservation`), secret redaction, and health/readiness probes are **implemented**. Distributed tracing backends (OpenTelemetry collector), long-term metrics storage (Prometheus), and alert manager dashboards are **planned**.

## Request Correlation and Tracing

Every HTTP request receives a server-generated UUID. It is traced across the pipeline:

`request -> embedding -> retrieval -> context -> generation -> response`

Available correlation fields:
- `request_id` in structured logs across all stages
- `X-Request-ID` in HTTP response headers
- `detail.request_id` in handled error responses
- `RequestObservation.request_id` in telemetry records

## Structured Events and Telemetry

The root logger emits compact JSON lines to standard output/error via `JsonFormatter`. Implemented event categories include:

| Event | Fields beyond common log metadata |
| --- | --- |
| `request` | `request_id`, method, path, status code, duration_ms |
| `retrieval` | `request_id`, result count, `embedding_ms`, `retrieval_ms` |
| `generation` | `request_id`, model, `generation_ms`, `input_tokens`, `output_tokens` |
| `retry_attempt` | `operation`, attempt number, backoff delay seconds, exception type |
| `retry_failure` | `operation`, max attempts reached, is_retryable flag, error type |
| `failure` | `request_id`, path, HTTP status, typed error category |

### Typed Structured Observations

Internal pipeline instrumentation uses `RequestObservation`:
- `request_id`: unique trace identifier
- `retrieval`: document IDs, chunk IDs, similarity scores, timing
- `generation`: model identifier, token counts, generation timing
- `timing`: embedding, retrieval, generation, total latency
- `outcome`: `"success"` or `"error"`, with error code classification

Observation data is strictly separated from public API response schemas to avoid leaking internal instrumentation fields.

## Health and Readiness Probes

Health checking is bifurcated to avoid expensive, cascaded dependency probes:

- **`GET /health` (Liveness)**: Fast check verifying that the application event loop is responsive. Returns `{"status": "ok"}`.
- **`GET /ready` (Readiness)**: Verifies that required local services (embedding model loaded, vector store initialized, pipeline instantiated) are ready to serve queries. Returns `200 OK` when ready, or `503 Service Unavailable` if uninitialized.

## Sensitive Content and Credential Redaction

`JsonFormatter` applies recursive redaction via `sanitize_log_value()`:
- Keys matching `authorization`, `api_key`, `apikey`, `secret`, `password`, `token`, `credential` are automatically replaced with `[REDACTED]`.
- Strings matching Bearer tokens (`Bearer ...`) or API key prefixes (`sk-...`) are sanitized.
- Complete document payloads and user queries are omitted from audit log bodies.

## Failure Taxonomy

Request and evaluation failures are categorized into a standardized taxonomy:
1. `validation_failure`: malformed requests or schema violations
2. `embedding_failure`: inference failures during query or document embedding
3. `retrieval_failure`: vector store connection refusal or search failure
4. `generation_failure`: empty answer or failure to satisfy required facts
5. `grounding_failure`: generated answers containing claims unsupported by retrieved context
6. `context_failure`: retrieved context relevance below acceptable threshold
7. `timeout`: external network operation exceeded timeout deadline
8. `provider_failure`: external LLM provider 5xx or unrecoverable error
