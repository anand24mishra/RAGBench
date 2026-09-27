from __future__ import annotations

import os
from pathlib import Path

import certifi
import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from evaluation.runner import REPOSITORY_ROOT, EvaluationConfig

# Ensure SSL certificate bundle is available on macOS / custom environments
os.environ.setdefault("SSL_CERT_FILE", certifi.where())


class ControlledExperimentError(ValueError):
    """Raised when an experiment alters multiple variable families simultaneously."""


class ExperimentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experiment_id: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    hypothesis: str | None = None
    changed_parameter: str | None = None
    questions_path: Path = Path("evaluation/dataset/questions.jsonl")
    dataset_metadata_path: Path = Path("evaluation/dataset/metadata.json")
    corpus_path: Path = Path("evaluation/dataset/corpus")
    result_path: Path | None = None
    summary_path: Path | None = None
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", min_length=1)
    embedding_batch_size: int = Field(default=32, gt=0)
    chunk_size: int = Field(gt=0)
    chunk_overlap: int = Field(ge=0)
    top_k: int = Field(ge=1, le=100)
    qdrant_mode: str = "memory"
    collection_name: str | None = None

    @model_validator(mode="after")
    def validate_configuration(self) -> ExperimentConfig:
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        if self.qdrant_mode != "memory":
            raise ValueError("Evaluation supports qdrant_mode=memory only")
        if not self.experiment_id.strip():
            raise ValueError("experiment_id must not be empty")
        if not self.dataset_version.strip():
            raise ValueError("dataset_version must not be empty")
        if not self.embedding_model.strip():
            raise ValueError("embedding_model must not be empty")
        return self

    def resolve_paths(self, repository_root: Path = REPOSITORY_ROOT) -> ExperimentConfig:
        data = self.model_dump()
        result_path = data["result_path"] or Path(f"evaluation/reports/{self.experiment_id}.json")
        summary_path = data["summary_path"] or Path(f"evaluation/reports/{self.experiment_id}.md")
        collection_name = (
            data["collection_name"] or f"ragbench_exp_{self.experiment_id.replace('-', '_')}"
        )

        data["result_path"] = result_path
        data["summary_path"] = summary_path
        data["collection_name"] = collection_name

        for field_name in (
            "questions_path",
            "dataset_metadata_path",
            "corpus_path",
            "result_path",
            "summary_path",
        ):
            path = data[field_name]
            if not path.is_absolute():
                data[field_name] = repository_root / path

        return ExperimentConfig.model_validate(data)

    def to_evaluation_config(self, repository_root: Path = REPOSITORY_ROOT) -> EvaluationConfig:
        resolved = self.resolve_paths(repository_root)
        return EvaluationConfig(
            experiment_id=resolved.experiment_id,
            dataset_version=resolved.dataset_version,
            questions_path=resolved.questions_path,
            dataset_metadata_path=resolved.dataset_metadata_path,
            corpus_path=resolved.corpus_path,
            result_path=resolved.result_path,
            summary_path=resolved.summary_path,
            embedding_model=resolved.embedding_model,
            embedding_batch_size=resolved.embedding_batch_size,
            chunk_size=resolved.chunk_size,
            chunk_overlap=resolved.chunk_overlap,
            top_k=resolved.top_k,
            qdrant_mode=resolved.qdrant_mode,
            collection_name=resolved.collection_name,
        )


def load_experiment_config(path: Path) -> ExperimentConfig:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError(f"Config content in {path} must be a YAML mapping")
        return ExperimentConfig.model_validate(raw).resolve_paths(REPOSITORY_ROOT)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        raise ValueError(f"Invalid experiment configuration: {path}") from exc


def validate_controlled_experiment(
    baseline: ExperimentConfig | EvaluationConfig,
    experiment: ExperimentConfig | EvaluationConfig,
) -> list[str]:
    """Verify that at most one variable family changed compared to baseline."""
    if baseline.dataset_version != experiment.dataset_version:
        raise ControlledExperimentError(
            f"Cannot compare experiments across different dataset versions "
            f"('{baseline.dataset_version}' vs '{experiment.dataset_version}')"
        )

    changed_variables: list[str] = []

    # 1. Chunking family
    if (
        baseline.chunk_size != experiment.chunk_size
        or baseline.chunk_overlap != experiment.chunk_overlap
    ):
        changed_variables.append("chunking")

    # 2. Top-k retrieval depth
    if baseline.top_k != experiment.top_k:
        changed_variables.append("top_k")

    # 3. Embedding model
    if baseline.embedding_model != experiment.embedding_model:
        changed_variables.append("embedding_model")

    # 4. Embedding batch size
    if baseline.embedding_batch_size != experiment.embedding_batch_size:
        changed_variables.append("embedding_batch_size")

    if len(changed_variables) > 1:
        raise ControlledExperimentError(
            f"Controlled experiment violation: multiple variables changed simultaneously "
            f"({', '.join(changed_variables)}). An experiment must vary only ONE parameter family."
        )

    return changed_variables
