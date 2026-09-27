# Benchmarking

## Status

Benchmark runner (`benchmarks/runner.py`), latency aggregation (`benchmarks/timing.py`), controlled concurrency benchmark (`benchmarks/concurrency.py`), provider-neutral cost accounting (`ragbench/cost/`), and reliability tracking are **implemented**. Distributed multi-node load generators and live process memory profiling are **planned**.

## Measurements

| Measurement | Status | Boundary |
| --- | --- | --- |
| Query Embedding Latency | Implemented | Monotonic clock around query embedding inference |
| Vector Retrieval Latency | Implemented | Monotonic clock around Qdrant search call |
| Generation Latency | Implemented | Dispatched LLM provider prompt to parsed answer |
| End-to-End Query Latency | Implemented | Query entry through answer assembly |
| Cold-start Initialization | Implemented | Model download, weight load, and collection setup |
| Steady-state Percentiles | Implemented | Percentiles (mean, p50, p95, p99) post-warmup |
| Concurrency & Throughput | Implemented | Queries per second under concurrency = 1, 5, 10 |
| Token Usage | Implemented | Input, output, and total token accounting |
| Cost per Query | Implemented | Versioned model pricing applied to token consumption |
| Failure & Timeout Rates | Implemented | Request success, failure rate, and timeout counts |
| Process Memory / CPU | Planned | Operating system cgroup / RSS memory monitoring |

## Latency Model & Methodology

Every benchmark run strictly isolates cold-start initialization from steady-state measurements:

1. **Environment Capture**: Python version, OS release, CPU architecture, detected accelerator (`cpu`, `mps`, `cuda`), software package versions.
2. **Warmup Phase**: Configurable warm-up passes (default: 2 passes across benchmark dataset) ensure model weights are cached in memory and JIT execution paths are primed.
3. **Steady-state Measurement**: Repeated passes across the dataset (default: 5 passes) compute linear percentile interpolation via `numpy.percentile` for p50, p95, and p99.
4. **Stage Attribution**: Each query isolates embedding time, vector search time, generation time, and total wall-clock time.

## Concurrency and CPU Contention

The controlled concurrency benchmark (`run_concurrency_benchmark`) evaluates throughput and latency degradation under concurrent request loads:

- Concurrency levels: `1`, `5`, `10`
- Semaphore-bounded asynchronous dispatch
- Measures throughput (QPS), latency percentiles, and failure rate

### Known Architectural Characteristic: In-Process Embedding Contention

In RAGBench, embedding inference (`sentence-transformers`) executes inside the application process. Under multi-client concurrency:
- Asynchronous retrieval I/O yields the event loop, but CPU-bound PyTorch embedding inference competes across OS threads.
- P95 latency scales non-linearly when concurrency exceeds available physical CPU cores.
- For high-concurrency production deployments, offloading embedding inference to a dedicated embedding microservice (e.g. Triton or TEI) is planned.

## Cost and Token Accounting Methodology

Cost accounting operates through `PricingRegistry` (`data/pricing.yaml`):

$$\text{Input Cost} = \frac{\text{Input Tokens}}{1{,}000{,}000} \times \text{Input Price per 1M}$$
$$\text{Output Cost} = \frac{\text{Output Tokens}}{1{,}000{,}000} \times \text{Output Price per 1M}$$
$$\text{Total Cost} = \text{Input Cost} + \text{Output Cost}$$
$$\text{Cost per Query} = \frac{\text{Total Cost}}{\text{Total Queries}}$$

If a model is unlisted in the pricing configuration or token counts are missing, the system records `cost_status: unavailable` and leaves monetary metrics as `null`. No arbitrary estimates or random numbers are fabricated.

## Reliability and Failure Accounting

Benchmark and evaluation runs capture:
- `total_requests`: total queries executed
- `successful_requests`: queries completing with valid, non-empty answers
- `failed_requests`: queries triggering retrieval, context, generation, grounding, or provider failures
- `failure_rate`: $\frac{\text{failed\_requests}}{\text{total\_requests}}$
- `timeouts`: count of network deadline timeouts
- `provider_errors`: count of upstream LLM 5xx or connection drops
