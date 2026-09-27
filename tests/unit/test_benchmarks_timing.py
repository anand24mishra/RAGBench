import pytest

from benchmarks.runner import get_benchmark_environment
from benchmarks.timing import (
    ExperimentTimingResult,
    LatencyStats,
    QueryLatency,
    calculate_latency_stats,
)


def test_aggregate_timings_and_percentiles() -> None:
    # 10 sorted numbers: 10, 20, 30, 40, 50, 60, 70, 80, 90, 100
    latencies = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
    stats = calculate_latency_stats(latencies)

    assert stats.sample_size == 10
    assert stats.mean_ms == 55.0
    assert stats.p50_ms == 55.0
    assert stats.min_ms == 10.0
    assert stats.max_ms == 100.0
    assert stats.p95_ms > 90.0
    assert stats.p99_ms > stats.p95_ms


def test_empty_timing_handling() -> None:
    with pytest.raises(
        ValueError, match="Cannot calculate latency statistics for an empty sequence"
    ):
        calculate_latency_stats([])


def test_timing_serialization_and_round_trip() -> None:
    stats = LatencyStats(
        sample_size=3,
        mean_ms=15.0,
        p50_ms=15.0,
        p95_ms=19.0,
        p99_ms=19.8,
        min_ms=10.0,
        max_ms=20.0,
    )
    query_latency = QueryLatency(
        query_id="q001",
        embedding_ms=12.5,
        retrieval_ms=2.5,
        total_ms=15.0,
    )
    timing = ExperimentTimingResult(
        sample_size=1,
        embedding_latency=stats,
        retrieval_latency=stats,
        total_runtime_ms=25.0,
        query_latencies=[query_latency],
    )

    serialized = timing.model_dump(mode="json")
    deserialized = ExperimentTimingResult.model_validate(serialized)

    assert deserialized == timing
    assert deserialized.embedding_latency.mean_ms == 15.0
    assert len(deserialized.query_latencies) == 1
    assert deserialized.query_latencies[0].query_id == "q001"


def test_benchmark_environment_capture() -> None:
    env = get_benchmark_environment()
    assert env.python_version != ""
    assert env.os_name != ""
    assert env.cpu_architecture != ""
    assert env.available_accelerator in ("cpu", "cuda", "mps")
    assert "ragbench" in env.software_versions
