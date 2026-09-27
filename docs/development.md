# Development

## Python and dependencies

RAGBench requires Python 3.11 or newer. The package, test, and lint configuration is in `pyproject.toml`; dependencies are declared in `requirements.txt`.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e . -r requirements.txt
```

Editable package installation has been verified with Python 3.13.6. CI runs Python 3.11.

## Configuration

Copy the placeholder environment file and provide a real provider key locally:

```bash
cp .env.example .env
```

`.env` is ignored by Git. The typed settings model validates integer ranges, LLM settings, and the relationship between chunk size and overlap. See [Deployment](deployment.md#environment-variables) for the full variable table.

## Formatting and linting

Ruff is configured for Python 3.11 with import, upgrade, bug-risk, and async checks:

```bash
ruff format .
ruff check --fix .
```

CI uses non-mutating checks:

```bash
ruff format --check .
ruff check .
```

Both checks pass on the current tree.

## Testing

```bash
pytest
```

The current suite contains 61 passing tests. It is divided into:

- unit tests for the loader, chunker, embedding adapter contract, context builder, schemas, retriever, pipeline, and provider parser;
- an ingestion-to-Qdrant retrieval integration test using Qdrant's in-memory client; and
- API integration tests using deterministic embeddings, an in-memory vector store, and a fake LLM; and
- evaluation tests for dataset validation, metrics, failure records, serialization, and comparison.

The suite does not download an embedding model, start Docker, or call a paid LLM. These substitutions keep CI deterministic while exercising the production interfaces.

## Running the API

Start Qdrant:

```bash
docker compose up -d qdrant
```

Set `LLM_API_KEY` in `.env`, then run:

```bash
uvicorn ragbench.app.main:app --reload
```

The application initializes the embedding model and checks or creates the Qdrant collection during startup. Startup fails when the model cannot load, Qdrant is unavailable, collection dimensions conflict, or the provider configuration is missing.

## Ingesting a document

```bash
python scripts/ingest.py path/to/document.md
```

Set `RAGBENCH_API_URL` or pass `--api-url` if the API is not available at `http://localhost:8000`.

## Running evaluation

Run the baseline with:

```bash
python -m ragbench.eval
```

This writes `evaluation/reports/baseline.json` and `evaluation/reports/baseline.md`. Pass `--config` for another experiment. Use `--compare BASELINE EXPERIMENT` to calculate metric deltas. The runner uses the configured sentence-transformer and in-memory Qdrant, but it does not call the LLM provider.

## Running benchmarks

Not implemented. Per-request latency fields exist, but there is no workload runner.

## Docker usage

Validate the resolved Compose file without starting services:

```bash
LLM_API_KEY=test-placeholder docker compose config --quiet
```

Start the stack using a real key from the environment or `.env`:

```bash
docker compose up --build
```

The Compose configuration has been validated locally. External LLM generation has not been tested without a user-supplied credential.
