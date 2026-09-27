# Deployment

## Status

Local Python execution, a Docker image definition, a two-service Docker Compose stack, container health checks, and a GitHub Actions verification workflow are implemented. No cloud deployment exists.

## Local

The local topology is one Uvicorn process connected to Qdrant over HTTP. The sentence-transformer model is loaded in the API process. An external OpenAI-compatible endpoint supplies generation.

The application startup sequence is:

1. validate environment-backed settings;
2. load the sentence-transformer model;
3. connect to Qdrant and create or validate the collection; and
4. validate the LLM provider selection and API key.

Failure in any step prevents the service from reporting healthy.

## Docker

The Dockerfile uses `python:3.11-slim`, installs the package and declared dependencies, runs as UID 10001, exposes port 8000, and starts Uvicorn. It does not contain an API key.

`docker-compose.yml` starts:

- `api`, built from the repository and exposed on port 8000; and
- `qdrant`, pinned to `qdrant/qdrant:v1.15.4`, exposed on port 6333 with a named persistence volume.

The API waits for the Qdrant health condition and has an HTTP health check against `/health`. Compose requires `LLM_API_KEY` from the environment or `.env` before rendering the API service.

The Compose configuration has been validated with `docker compose config --quiet`. A full image build and external generation call are not yet recorded as deployment evidence.

## CI

`.github/workflows/ci.yml` runs for pushes and pull requests on GitHub-hosted Ubuntu:
1. **test**: installs Python 3.11 dependencies, runs `ruff format --check .`, `ruff check .`, and `pytest`.
2. **regression-gate**: executes offline deterministic generation evaluation on dataset `1.1.0` and validates against regression policy thresholds using `python -m ragbench.regression_gate`.

CI does not require paid external LLM credentials.

## Health and Readiness Probes

Health checks are explicitly separated into liveness and readiness:

- **`GET /health` (Liveness)**: Fast probe verifying that the HTTP server and event loop are responsive. Returns `200 OK` with `{"status":"ok"}`. Recommended for Kubernetes `livenessProbe`.
- **`GET /ready` (Readiness)**: Probes whether local application services (`AppServices`) are instantiated, the embedding model dimension is confirmed, and the vector store is ready to serve. Returns `200 OK` with `{"status":"ready", "checks":{...}}`, or `503 Service Unavailable` if uninitialized. Recommended for Kubernetes `readinessProbe`.

Neither endpoint issues live external network probes to upstream LLM providers or remote Qdrant clusters on every health check, avoiding health-check cascading failures.

## Failure Handling and Retry Policies

1. **HTTP Boundary Mapping**:
   - `400 Bad Request`: malformed or unsupported document upload
   - `422 Unprocessable Content`: query validation failure or empty query
   - `502 Bad Gateway`: upstream embedding or vector store failure
   - `503 Service Unavailable`: readiness probe failed (services uninitialized)
   - `504 Gateway Timeout`: upstream LLM network timeout
2. **Bounded Retry Policy (`RetryPolicy`)**:
   - Upstream LLM provider requests apply exponential backoff (default max 3 attempts).
   - **Retryable Errors**: HTTP 429 (rate limits), transient 5xx (500, 502, 503, 504), network timeouts.
   - **Non-Retryable Errors**: HTTP 4xx (client errors, authorization failures), validation errors, and malformed responses fail immediately without retry amplification.
   - Network timeouts are explicit (`llm_timeout_seconds`, default 30s).

