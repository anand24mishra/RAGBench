from __future__ import annotations

import json
from pathlib import Path

from evaluation.comparison import compare_results, load_evaluation_result
from evaluation.models import ComparisonResult, EvaluationResult
from evaluation.runner import (
    DEFAULT_CONFIG,
    EvaluationConfig,
    load_config,
    run_evaluation,
)
from ragbench.experiments.config import (
    ExperimentConfig,
    validate_controlled_experiment,
)


def _generate_experiment_markdown(
    result: EvaluationResult,
    comparison: ComparisonResult | None,
    config: ExperimentConfig,
) -> str:
    scope_notice = (
        "Evaluated on the current 10-question repository-specific benchmark (5 documents). "
        "Results indicate behavior on this specific workload and are not broad statistical claims."
    )
    hypothesis_text = config.hypothesis or result.hypothesis or "No explicit hypothesis declared."
    param_text = config.changed_parameter or result.changed_parameter or "None"
    cfg = result.retriever_configuration

    lines = [
        f"# Experiment Report: `{result.experiment_id}`",
        "",
        f"- **Date:** {result.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"- **Dataset:** `{result.dataset_name}` version `{result.dataset_version}`",
        f"- **Dataset Fingerprint:** `{result.dataset_fingerprint}`",
        f"- **Dataset Scope Notice:** {scope_notice}",
        "",
        "## Hypothesis and Parameter Change",
        "",
        f"- **Hypothesis:** {hypothesis_text}",
        f"- **Changed Parameter:** `{param_text}`",
        "",
        "## Configuration",
        "",
        "| Parameter | Value |",
        "| --- | --- |",
        f"| Chunk Size | {cfg.chunk_size} characters |",
        f"| Chunk Overlap | {cfg.chunk_overlap} characters |",
        f"| Retrieval Depth (top-k) | {result.top_k} |",
        f"| Embedding Model | `{result.embedding_model}` |",
        f"| Embedding Dimension | {result.embedding_dimension or 'N/A'} |",
        f"| Embedding Batch Size | {cfg.embedding_batch_size} |",
        f"| Vector Store | {cfg.vector_store} ({cfg.qdrant_mode}) |",
        f"| Distance Metric | {cfg.distance} |",
        "",
        "## Retrieval Quality Metrics",
        "",
    ]

    if comparison is not None:
        lines.extend(
            [
                "| Metric | Baseline | Experiment | Delta |",
                "| --- | ---: | ---: | ---: |",
            ]
        )
        for name, comp in sorted(comparison.metrics.items()):
            sign = "+" if comp.delta > 0 else ""
            lines.append(
                f"| {name} | {comp.baseline:.6f} | {comp.experiment:.6f} | {sign}{comp.delta:.6f} |"
            )
        lines.append("")
    else:
        lines.extend(
            [
                "| Metric | Result |",
                "| --- | ---: |",
                f"| Recall@1 | {result.metrics['recall_at_1']:.6f} |",
                f"| Recall@3 | {result.metrics['recall_at_3']:.6f} |",
                f"| Recall@5 | {result.metrics['recall_at_5']:.6f} |",
                f"| MRR | {result.metrics['mrr']:.6f} |",
                "",
            ]
        )

    if result.top_k < 5:
        topk_note = (
            f"> **Note on Top-k semantics:** When retrieval depth top_k is configured below 5, "
            f"the candidate pool is capped at {result.top_k} chunks. Metrics Recall@3 and Recall@5 "
            "are calculated on the retrieved candidate set; because fewer than 5 items are "
            "retrieved, relevant items outside the retrieved top_k cannot be recalled at cutoff 5."
        )
        lines.extend([topk_note, ""])

    lines.extend(
        [
            "## Performance & Latency Measurements",
            "",
        ]
    )

    if result.timing is not None:
        emb = result.timing.embedding_latency
        ret = result.timing.retrieval_latency
        lines.extend(
            [
                f"- **Sample size:** {result.timing.sample_size} queries",
                f"- **Total evaluation runtime:** {result.timing.total_runtime_ms:.2f} ms",
                "",
                "| Phase | Mean (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Min (ms) | Max (ms) |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
                (
                    f"| Query Embedding | {emb.mean_ms:.3f} | {emb.p50_ms:.3f} | "
                    f"{emb.p95_ms:.3f} | {emb.p99_ms:.3f} | {emb.min_ms:.3f} | {emb.max_ms:.3f} |"
                ),
                (
                    f"| Vector Retrieval | {ret.mean_ms:.3f} | {ret.p50_ms:.3f} | "
                    f"{ret.p95_ms:.3f} | {ret.p99_ms:.3f} | {ret.min_ms:.3f} | {ret.max_ms:.3f} |"
                ),
                "",
            ]
        )
    else:
        lines.extend(["Timing measurements were not captured for this run.", ""])

    lines.extend(
        [
            "## Ranking Changes & Observed Retrieval Failures",
            "",
        ]
    )

    if comparison is not None and comparison.ranking_changes:
        rank_header = (
            "| Query ID | Expected Document | Baseline Rank | Experiment Rank | "
            "Baseline Score | Experiment Score |"
        )
        lines.extend(
            [
                f"### Observed Rank Movements ({len(comparison.ranking_changes)} document changes)",
                "",
                rank_header,
                "| --- | --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for change in comparison.ranking_changes:
            base_r = (
                str(change.baseline_rank) if change.baseline_rank is not None else "Not in top-k"
            )
            exp_r = (
                str(change.experiment_rank)
                if change.experiment_rank is not None
                else "Not in top-k"
            )
            base_s = f"{change.baseline_score:.4f}" if change.baseline_score is not None else "N/A"
            exp_s = (
                f"{change.experiment_score:.4f}" if change.experiment_score is not None else "N/A"
            )
            lines.append(
                f"| `{change.query_id}` | `{change.expected_document}` | "
                f"{base_r} | {exp_r} | {base_s} | {exp_s} |"
            )
        lines.append("")
    elif comparison is not None:
        lines.extend(
            ["No relevant document rank movements observed between baseline and experiment.", ""]
        )

    if result.failures:
        lines.extend(
            [
                f"### Unretrieved Documents at top_k={result.top_k} "
                f"({len(result.failures)} failures)",
                "",
                "| Query ID | Missing Expected Document | Retrieved Document Candidates |",
                "| --- | --- | --- |",
            ]
        )
        for failure in result.failures:
            retrieved_str = ", ".join(f"`{d}`" for d in failure.retrieved_documents)
            lines.append(
                f"| `{failure.query_id}` | `{failure.expected_document}` | {retrieved_str} |"
            )
        lines.append("")
    else:
        lines.extend(
            [
                f"Zero retrieval failures: all relevant documents were present within the "
                f"top-{result.top_k} results.",
                "",
            ]
        )

    # Interpretation and decision
    interpretation = (
        result.interpretation or "Requires a larger evaluation set and further investigation."
    )
    decision = result.decision or "Retain for further investigation"

    lines.extend(
        [
            "## Interpretation and Decision",
            "",
            f"- **Interpretation:** {interpretation}",
            f"- **Decision:** {decision}",
            "",
            "Generation evaluation: Not implemented.",
            "",
        ]
    )

    return "\n".join(lines)


async def run_experiment(
    config: ExperimentConfig,
    baseline_config: ExperimentConfig | EvaluationConfig | None = None,
    write_reports: bool = True,
    allow_multiple_variables: bool = False,
) -> tuple[EvaluationResult, ComparisonResult | None]:
    resolved_config = config.resolve_paths()

    # Load baseline config if not explicitly passed
    if baseline_config is None and DEFAULT_CONFIG.exists():
        try:
            baseline_config = load_config(DEFAULT_CONFIG)
        except Exception:
            baseline_config = None

    if baseline_config is not None and not allow_multiple_variables:
        validate_controlled_experiment(baseline_config, resolved_config)

    eval_config = resolved_config.to_evaluation_config()
    result = await run_evaluation(eval_config)

    # Attach experiment metadata
    result = result.model_copy(
        update={
            "schema_version": "3",
            "hypothesis": resolved_config.hypothesis,
            "changed_parameter": resolved_config.changed_parameter,
        }
    )

    comparison: ComparisonResult | None = None
    baseline_report_path = (
        baseline_config.result_path
        if baseline_config and baseline_config.result_path.exists()
        else Path("evaluation/reports/baseline.json")
    )
    if baseline_report_path.exists() and resolved_config.experiment_id != "v2-baseline":
        try:
            baseline_result = load_evaluation_result(baseline_report_path)
            comparison = compare_results(baseline_result, result)
        except Exception:
            comparison = None

    # Derive neutral interpretation and decision based on measured metrics
    if comparison is not None:
        rec5_delta = comparison.metrics.get("recall_at_5", None)
        mrr_delta = comparison.metrics.get("mrr", None)

        if rec5_delta and rec5_delta.delta < 0:
            interpretation = (
                f"On the current 10-question repository-specific benchmark, Recall@5 degraded by "
                f"{abs(rec5_delta.delta):.4f}. The candidate configuration dropped evidence."
            )
            decision = "Reject for this workload"
        elif mrr_delta and mrr_delta.delta > 0:
            interpretation = (
                f"On the current 10-question repository-specific benchmark, MRR shifted by "
                f"+{mrr_delta.delta:.4f}. Directional change noted; "
                "sample size is not statistically representative."
            )
            decision = "Retain for further investigation"
        elif mrr_delta and mrr_delta.delta < 0:
            interpretation = (
                f"On the current 10-question repository-specific benchmark, MRR shifted by "
                f"{mrr_delta.delta:.4f}. Retrieval ranking lowered without improving top-k recall."
            )
            decision = "Reject for this workload"
        else:
            interpretation = (
                "On the current 10-question repository-specific benchmark, retrieval quality "
                "metrics matched baseline exactly. Latency and granularity trade-offs guide fit."
            )
            decision = "Retain for further investigation"
    else:
        interpretation = (
            "Baseline report unavailable for delta calculation. On the current 10-question "
            "repository-specific benchmark, metrics provide reference measurements."
        )
        decision = "Requires a larger evaluation set"

    result = result.model_copy(
        update={
            "interpretation": interpretation,
            "decision": decision,
        }
    )

    if write_reports and resolved_config.result_path and resolved_config.summary_path:
        # Write machine-readable json
        resolved_config.result_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_config.result_path.write_text(
            json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        # Write human-readable markdown
        markdown_content = _generate_experiment_markdown(result, comparison, resolved_config)
        resolved_config.summary_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_config.summary_path.write_text(markdown_content, encoding="utf-8")

    return result, comparison
