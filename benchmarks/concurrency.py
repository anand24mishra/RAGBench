from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from time import perf_counter

from pydantic import BaseModel, ConfigDict, Field

from benchmarks.timing import LatencyStats, calculate_latency_stats
from ragbench.app.pipeline.rag import RAGPipeline


class ConcurrencyLevelResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    concurrency: int = Field(ge=1)
    total_queries: int = Field(ge=1)
    successful_queries: int = Field(ge=0)
    failed_queries: int = Field(ge=0)
    failure_rate: float = Field(ge=0.0, le=1.0)
    duration_seconds: float = Field(ge=0.0)
    throughput_qps: float = Field(ge=0.0)
    latency_stats: LatencyStats
    notes: str | None = None


class ConcurrencyBenchmarkResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    benchmark_id: str
    timestamp: datetime
    levels: list[ConcurrencyLevelResult]
    cpu_competition_noted: bool = True
    summary: str


async def run_concurrency_benchmark(
    pipeline: RAGPipeline,
    questions: list[str],
    concurrency_levels: list[int] | None = None,
    queries_per_level: int = 20,
    benchmark_id: str = "concurrency-benchmark",
) -> ConcurrencyBenchmarkResult:
    """Executes controlled concurrency benchmark across specified concurrency levels.

    Exposes in-process CPU contention during concurrent local embedding inference.
    """
    levels_to_test = concurrency_levels or [1, 5, 10]
    results: list[ConcurrencyLevelResult] = []

    for concurrency in levels_to_test:
        semaphore = asyncio.Semaphore(concurrency)
        latencies: list[float] = []
        successes = 0
        failures = 0

        # Cycle questions to reach queries_per_level
        q_subset = [questions[i % len(questions)] for i in range(queries_per_level)]

        async def _worker(
            query_text: str,
            idx: int,
            sem: asyncio.Semaphore = semaphore,
            conc: int = concurrency,
            lats: list[float] = latencies,
        ) -> None:
            nonlocal successes, failures
            async with sem:
                req_start = perf_counter()
                try:
                    await pipeline.query(query_text, top_k=5, request_id=f"c{conc}_q{idx}")
                    lats.append((perf_counter() - req_start) * 1000)
                    successes += 1
                except Exception:
                    failures += 1

        bench_start = perf_counter()
        await asyncio.gather(*[_worker(q, i) for i, q in enumerate(q_subset)])
        duration = perf_counter() - bench_start

        throughput = successes / duration if duration > 0 else 0.0
        stats = (
            calculate_latency_stats(latencies)
            if latencies
            else LatencyStats(
                sample_size=0,
                mean_ms=0,
                p50_ms=0,
                p95_ms=0,
                p99_ms=0,
                min_ms=0,
                max_ms=0,
            )
        )
        fail_rate = failures / queries_per_level if queries_per_level > 0 else 0.0

        notes = None
        if concurrency > 1 and len(results) > 0:
            c1_p95 = results[0].latency_stats.p95_ms
            if stats.p95_ms > c1_p95 * 1.5:
                ratio = stats.p95_ms / c1_p95
                notes = (
                    f"P95 latency elevated by {ratio:.1f}x under concurrency {concurrency} "
                    "due to in-process CPU embedding competition."
                )

        results.append(
            ConcurrencyLevelResult(
                concurrency=concurrency,
                total_queries=queries_per_level,
                successful_queries=successes,
                failed_queries=failures,
                failure_rate=round(fail_rate, 4),
                duration_seconds=round(duration, 3),
                throughput_qps=round(throughput, 2),
                latency_stats=stats,
                notes=notes,
            )
        )

    summary = (
        f"Concurrency benchmark completed across levels {levels_to_test}. "
        f"Max throughput: {max(r.throughput_qps for r in results):.1f} QPS."
    )

    return ConcurrencyBenchmarkResult(
        benchmark_id=benchmark_id,
        timestamp=datetime.now(UTC),
        levels=results,
        cpu_competition_noted=True,
        summary=summary,
    )
