from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from evaluation.comparison import load_evaluation_result
from ragbench.regression.engine import evaluate_regression
from ragbench.regression.models import RegressionPolicy
from ragbench.regression.report import format_markdown_regression_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="RAGBench Regression Gate: quality, latency, cost, and reliability"
    )
    parser.add_argument("--baseline", type=Path, required=True, help="Baseline JSON report")
    parser.add_argument("--candidate", type=Path, required=True, help="Candidate JSON report")
    parser.add_argument("--policy", type=Path, default=None, help="Optional policy YAML path")
    parser.add_argument("--output-json", type=Path, default=None, help="Output JSON path")
    parser.add_argument("--output-md", type=Path, default=None, help="Output Markdown report path")

    args = parser.parse_args(argv)

    baseline = load_evaluation_result(args.baseline)
    candidate = load_evaluation_result(args.candidate)

    policy = None
    if args.policy and args.policy.is_file():
        raw_policy = yaml.safe_load(args.policy.read_text(encoding="utf-8"))
        if isinstance(raw_policy, dict):
            policy = RegressionPolicy.model_validate(raw_policy)

    decision = evaluate_regression(baseline, candidate, policy)

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(decision.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(
            format_markdown_regression_report(decision),
            encoding="utf-8",
        )

    # Print summary
    print(decision.summary)
    for c in decision.checks:
        print(f"[{c.status.upper():12}] {c.category:12} {c.metric:22} | {c.message}")

    if decision.status == "pass":
        return 0
    if decision.status == "fail":
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
