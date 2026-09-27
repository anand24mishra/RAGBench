from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from evaluation.runner import REPOSITORY_ROOT

DEFAULT_REGISTRY_PATH = REPOSITORY_ROOT / "experiments" / "registry.yaml"


class ExperimentRegistryEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    type: Literal["chunking", "top_k", "embeddings", "baseline"]
    config: Path


class ExperimentRegistry(BaseModel):
    model_config = ConfigDict(frozen=True)

    experiments: list[ExperimentRegistryEntry] = Field(default_factory=list)


def load_registry(path: Path = DEFAULT_REGISTRY_PATH) -> ExperimentRegistry:
    if not path.exists():
        raise FileNotFoundError(f"Registry file not found: {path}")

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "experiments" not in raw:
        raise ValueError(f"Invalid registry format in {path}: expected 'experiments' list")

    entries = [ExperimentRegistryEntry.model_validate(item) for item in raw["experiments"]]
    return ExperimentRegistry(experiments=entries)
