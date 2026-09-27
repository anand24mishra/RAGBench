from __future__ import annotations

from ragbench.regression.models import RegressionDecision


def format_markdown_regression_report(decision: RegressionDecision) -> str:
    status_badge = {
        "pass": "PASSED",
        "fail": "FAILED",
        "inconclusive": "INCONCLUSIVE",
    }.get(decision.status, decision.status.upper())

    lines: list[str] = [
        f"# RAGBench Regression Gate Report: {status_badge}",
        "",
        f"- **Status**: `{decision.status}`",
        f"- **Baseline ID**: `{decision.baseline_id}`",
        f"- **Candidate ID**: `{decision.candidate_id}`",
        f"- **Dataset Version**: `{decision.dataset_version}`",
        f"- **Summary**: {decision.summary}",
        "",
    ]

    if decision.warnings:
        lines.append("## Warnings")
        lines.append("")
        for w in decision.warnings:
            lines.append(f"- :warning: {w}")
        lines.append("")

    lines.append("## Regression Checks")
    lines.append("")
    lines.append("| Category | Metric | Baseline | Candidate | Delta | Threshold | Status |")
    lines.append("|---|---|---|---|---|---|---|")

    for c in decision.checks:
        b_str = f"{c.baseline}" if c.baseline is not None else "-"
        c_str = f"{c.candidate}" if c.candidate is not None else "-"
        d_str = f"{c.delta:+.4f}" if c.delta is not None else "-"
        t_str = f"{c.threshold}" if c.threshold is not None else "-"
        status_md = f"**{c.status.upper()}**"
        lines.append(
            f"| {c.category} | `{c.metric}` | {b_str} | {c_str} | {d_str} | {t_str} | {status_md} |"
        )
    lines.append("")

    if decision.diagnostics:
        lines.append("## Regressed Query Diagnostics")
        lines.append("")
        for d in decision.diagnostics:
            lines.append(f"### Query `{d.query_id}`")
            lines.append(f"- **Question**: {d.question}")
            lines.append(f"- **Reason**: {d.reason}")
            lines.append(f"- **Relevant Documents**: `{d.relevant_documents}`")
            lines.append(f"- **Retrieved Documents**: `{d.retrieved_documents}`")
            if d.baseline_answer:
                lines.append(f"- **Baseline Answer**: {d.baseline_answer}")
            if d.candidate_answer:
                lines.append(f"- **Candidate Answer**: {d.candidate_answer}")
            if d.reference_answer:
                lines.append(f"- **Reference Answer**: {d.reference_answer}")
            lines.append("")

    return "\n".join(lines) + "\n"
