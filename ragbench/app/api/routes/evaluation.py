from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

REPORTS_DIR = Path(__file__).resolve().parents[4] / "evaluation" / "reports"


def _read_report_json(filename: str) -> dict[str, Any]:
    path = REPORTS_DIR / filename
    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report file '{filename}' was not found.",
        )
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read report '{filename}': {exc}",
        ) from exc


@router.get("/baseline")
async def get_baseline() -> dict[str, Any]:
    """Return the baseline evaluation report."""
    return _read_report_json("baseline.json")


@router.get("/generation-baseline")
async def get_generation_baseline() -> dict[str, Any]:
    """Return the baseline generation evaluation report."""
    return _read_report_json("generation_v4_baseline.json")


@router.get("/candidate")
async def get_candidate() -> dict[str, Any]:
    """Return the candidate generation evaluation report."""
    return _read_report_json("generation_v5_candidate.json")


@router.get("/regression")
async def get_regression_decision() -> dict[str, Any]:
    """Return the V5 regression evaluation decision."""
    return _read_report_json("regression_v5_decision.json")
