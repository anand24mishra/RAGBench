from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException, status

from evaluation.comparison import compare_results, load_evaluation_result

router = APIRouter(tags=["experiments"])

ROOT_DIR = Path(__file__).resolve().parents[4]
REGISTRY_PATH = ROOT_DIR / "experiments" / "registry.yaml"
REPORTS_DIR = ROOT_DIR / "evaluation" / "reports"
BASELINE_PATH = REPORTS_DIR / "baseline.json"
GEN_BASELINE_PATH = REPORTS_DIR / "generation_v4_baseline.json"


@router.get("/experiments")
async def list_experiments() -> list[dict[str, Any]]:
    """List registered experiments with evaluated metrics when available."""
    if not REGISTRY_PATH.is_file():
        return []

    try:
        raw = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8")) or {}
        registered = raw.get("experiments", [])
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read experiment registry: {exc}",
        ) from exc

    results: list[dict[str, Any]] = []
    for exp in registered:
        exp_id = exp.get("id")
        exp_type = exp.get("type", "unknown")
        config_path = exp.get("config")

        report_file = REPORTS_DIR / f"{exp_id}.json"
        metrics: dict[str, Any] | None = None
        timing: dict[str, Any] | None = None
        evaluated = False

        if report_file.is_file():
            try:
                data = json.loads(report_file.read_text(encoding="utf-8"))
                metrics = data.get("metrics")
                timing = data.get("timing")
                evaluated = True
            except Exception:
                pass

        results.append(
            {
                "id": exp_id,
                "type": exp_type,
                "config_path": config_path,
                "evaluated": evaluated,
                "metrics": metrics,
                "timing": timing,
            }
        )

    return results


@router.get("/experiments/{experiment_id}")
async def get_experiment(experiment_id: str) -> dict[str, Any]:
    """Get full evaluation report for an experiment."""
    report_file = REPORTS_DIR / f"{experiment_id}.json"
    if not report_file.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment '{experiment_id}' evaluation report was not found.",
        )
    try:
        return json.loads(report_file.read_text(encoding="utf-8"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse experiment report: {exc}",
        ) from exc


@router.get("/experiments/{experiment_id}/comparison")
async def get_experiment_comparison(experiment_id: str) -> dict[str, Any]:
    """Get comparison between an experiment and the baseline."""
    if not BASELINE_PATH.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Baseline evaluation report was not found.",
        )
    exp_path = REPORTS_DIR / f"{experiment_id}.json"
    if not exp_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment '{experiment_id}' was not found.",
        )

    try:
        baseline = load_evaluation_result(BASELINE_PATH)
        experiment = load_evaluation_result(exp_path)
        comparison = compare_results(baseline, experiment)
        return comparison.model_dump(mode="json")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute comparison: {exc}",
        ) from exc


@router.get("/inspect/{query_id}")
async def inspect_query(query_id: str) -> dict[str, Any]:
    """Get query trace details across baseline and generation evaluations."""
    baseline_query: dict[str, Any] | None = None
    gen_query: dict[str, Any] | None = None

    if BASELINE_PATH.is_file():
        try:
            base_data = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
            for q in base_data.get("queries", []):
                if q.get("query_id") == query_id:
                    baseline_query = q
                    break
        except Exception:
            pass

    if GEN_BASELINE_PATH.is_file():
        try:
            gen_data = json.loads(GEN_BASELINE_PATH.read_text(encoding="utf-8"))
            for q in gen_data.get("queries", []):
                if q.get("query_id") == query_id:
                    gen_query = q
                    break
        except Exception:
            pass

    if not baseline_query and not gen_query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query '{query_id}' was not found in evaluation datasets.",
        )

    return {
        "query_id": query_id,
        "baseline_retrieval": baseline_query,
        "generation_evaluation": gen_query,
    }
