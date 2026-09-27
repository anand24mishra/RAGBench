from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from benchmarks.runner import BenchmarkConfig, run_benchmark, write_benchmark_result
from evaluation.comparison import compare_results, load_evaluation_result, write_comparison
from evaluation.runner import REPOSITORY_ROOT
from ragbench.experiments.config import load_experiment_config
from ragbench.experiments.registry import DEFAULT_REGISTRY_PATH, load_registry
from ragbench.experiments.runner import run_experiment


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ragbench.experiments",
        description="RAGBench V3 Controlled Retrieval Experiments and Benchmarking",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # run command
    run_parser = subparsers.add_parser("run", help="Run a controlled retrieval experiment")
    run_parser.add_argument("config", type=Path, help="Path to experiment configuration YAML")
    run_parser.add_argument(
        "--baseline",
        type=Path,
        default=REPOSITORY_ROOT / "experiments" / "baseline" / "config.yaml",
        help="Path to baseline configuration YAML",
    )
    run_parser.add_argument(
        "--allow-multiple-variables",
        action="store_true",
        help="Override single-variable restriction",
    )

    # compare command
    compare_parser = subparsers.add_parser(
        "compare", help="Compare two evaluation/experiment result artifacts"
    )
    compare_parser.add_argument("baseline", type=Path, help="Baseline JSON report path")
    compare_parser.add_argument("experiment", type=Path, help="Experiment JSON report path")
    compare_parser.add_argument("--output", type=Path, help="Output comparison JSON path")

    # benchmark command
    bench_parser = subparsers.add_parser(
        "benchmark", help="Run latency benchmark on a configuration"
    )
    bench_parser.add_argument("config", type=Path, help="Path to configuration YAML")
    bench_parser.add_argument("--warmup", type=int, default=2, help="Number of warmup repetitions")
    bench_parser.add_argument(
        "--runs", type=int, default=5, help="Number of measurement repetitions"
    )
    bench_parser.add_argument("--output", type=Path, help="Path to write benchmark JSON report")

    # list command
    list_parser = subparsers.add_parser("list", help="List registered experiments")
    list_parser.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY_PATH,
        help="Path to registry YAML",
    )

    # run-all command
    run_all_parser = subparsers.add_parser("run-all", help="Execute all registered experiments")
    run_all_parser.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY_PATH,
        help="Path to registry YAML",
    )

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "run":
        config = load_experiment_config(args.config)
        baseline_config = None
        if args.baseline.exists():
            baseline_config = load_experiment_config(args.baseline)

        result, comparison = asyncio.run(
            run_experiment(
                config,
                baseline_config=baseline_config,
                allow_multiple_variables=args.allow_multiple_variables,
            )
        )

        print(f"RAGBench Experiment: {result.experiment_id}")
        print(
            f"Dataset: {result.dataset_name} "
            f"(v{result.dataset_version}, {result.query_count} queries)"
        )
        print(f"Embedding Model: {result.embedding_model} (dim={result.embedding_dimension})")
        cfg_ret = result.retriever_configuration
        print(f"Chunking: {cfg_ret.chunk_size}/{cfg_ret.chunk_overlap}")
        print(f"Top-k: {result.top_k}")
        print()
        print(f"Recall@1: {result.metrics['recall_at_1']:.6f}")
        print(f"Recall@3: {result.metrics['recall_at_3']:.6f}")
        print(f"Recall@5: {result.metrics['recall_at_5']:.6f}")
        print(f"MRR:      {result.metrics['mrr']:.6f}")
        if result.timing:
            emb_lat = result.timing.embedding_latency
            ret_lat = result.timing.retrieval_latency
            print(
                f"Embedding Latency (mean/p50/p95): {emb_lat.mean_ms:.2f}ms / "
                f"{emb_lat.p50_ms:.2f}ms / {emb_lat.p95_ms:.2f}ms"
            )
            print(
                f"Retrieval Latency (mean/p50/p95): {ret_lat.mean_ms:.2f}ms / "
                f"{ret_lat.p50_ms:.2f}ms / {ret_lat.p95_ms:.2f}ms"
            )
        print(f"Decision: {result.decision}")
        if comparison and comparison.ranking_changes:
            print(f"Ranking changes vs baseline: {len(comparison.ranking_changes)}")
        print(f"Report saved to: {config.result_path}")
        print(f"Summary saved to: {config.summary_path}")

    elif args.command == "compare":
        base_res = load_evaluation_result(args.baseline)
        exp_res = load_evaluation_result(args.experiment)
        comparison = compare_results(base_res, exp_res)
        if args.output:
            write_comparison(comparison, args.output)
        print(json.dumps(comparison.model_dump(mode="json"), indent=2, sort_keys=True))

    elif args.command == "benchmark":
        exp_config = load_experiment_config(args.config)
        eval_config = exp_config.to_evaluation_config()
        bench_config = BenchmarkConfig(warmup_runs=args.warmup, measurement_runs=args.runs)
        output_path = args.output or Path(f"benchmarks/reports/{exp_config.experiment_id}.json")
        result = asyncio.run(run_benchmark(eval_config, bench_config))
        write_benchmark_result(result, output_path)

        print(f"Benchmark: {result.benchmark_id}")
        print(f"Model Init Time: {result.model_initialization_ms:.2f}ms")
        emb_ss = result.steady_state_embedding_latency
        ret_ss = result.steady_state_retrieval_latency
        print(
            f"Steady-state Query Embedding: mean={emb_ss.mean_ms:.2f}ms, "
            f"p50={emb_ss.p50_ms:.2f}ms, p95={emb_ss.p95_ms:.2f}ms"
        )
        print(
            f"Steady-state Vector Retrieval: mean={ret_ss.mean_ms:.2f}ms, "
            f"p50={ret_ss.p50_ms:.2f}ms, p95={ret_ss.p95_ms:.2f}ms"
        )
        print(f"Total benchmark runtime: {result.total_benchmark_runtime_ms:.2f}ms")
        print(f"Output saved to: {output_path}")

    elif args.command == "list":
        reg = load_registry(args.registry)
        print(f"Registered experiments ({len(reg.experiments)}):")
        for entry in reg.experiments:
            print(f"  - [{entry.type}] {entry.id}: {entry.config}")

    elif args.command == "run-all":
        reg = load_registry(args.registry)
        baseline_config = None
        base_path = REPOSITORY_ROOT / "experiments" / "baseline" / "config.yaml"
        if base_path.exists():
            baseline_config = load_experiment_config(base_path)

        for entry in reg.experiments:
            config_path = entry.config
            if not config_path.is_absolute():
                config_path = REPOSITORY_ROOT / config_path
            cfg = load_experiment_config(config_path)
            print(f"Executing experiment {entry.id} ({entry.type})...")
            asyncio.run(run_experiment(cfg, baseline_config=baseline_config))
        print("All registered experiments executed successfully.")


if __name__ == "__main__":
    main()
