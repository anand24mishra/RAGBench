from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DatasetValidationError(ValueError):
    """Raised when an evaluation dataset cannot be validated."""


class EvaluationQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    relevant_documents: list[str] = Field(min_length=1)
    reference_answer: str | None = None
    required_facts: list[str] = Field(default_factory=list)

    @field_validator("id", "question")
    @classmethod
    def reject_blank_strings(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must contain non-whitespace text")
        return value

    @field_validator("relevant_documents")
    @classmethod
    def validate_relevant_documents(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values]
        if any(not value for value in normalized):
            raise ValueError("relevant document IDs must not be blank")
        if len(normalized) != len(set(normalized)):
            raise ValueError("relevant document IDs must be unique")
        return normalized

    @field_validator("reference_answer")
    @classmethod
    def normalize_reference_answer(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("reference_answer must be omitted rather than blank")
        return value

    @field_validator("required_facts")
    @classmethod
    def validate_required_facts(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values]
        if any(not value for value in normalized):
            raise ValueError("required facts must not contain blank text")
        return normalized


class DatasetMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = Field(min_length=1)
    name: str = Field(min_length=1)
    document_ids: list[str] = Field(min_length=1)

    @field_validator("document_ids")
    @classmethod
    def validate_document_ids(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values]
        if any(not value for value in normalized):
            raise ValueError("document IDs must not be blank")
        if len(normalized) != len(set(normalized)):
            raise ValueError("document IDs must be unique")
        return normalized


class EvaluationDataset(BaseModel):
    model_config = ConfigDict(frozen=True)

    version: str
    name: str
    questions: list[EvaluationQuestion]


def load_dataset(questions_path: Path, metadata_path: Path) -> EvaluationDataset:
    try:
        metadata = DatasetMetadata.model_validate_json(metadata_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise DatasetValidationError(f"Invalid dataset metadata: {metadata_path}") from exc

    questions: list[EvaluationQuestion] = []
    seen_ids: set[str] = set()
    try:
        lines = questions_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise DatasetValidationError(f"Cannot read evaluation questions: {questions_path}") from exc

    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            raw_record = json.loads(line)
            question = EvaluationQuestion.model_validate(raw_record)
        except (json.JSONDecodeError, ValueError) as exc:
            raise DatasetValidationError(
                f"Invalid evaluation record at {questions_path}:{line_number}"
            ) from exc
        if question.id in seen_ids:
            raise DatasetValidationError(f"Duplicate evaluation question ID: {question.id}")
        unknown_documents = set(question.relevant_documents) - set(metadata.document_ids)
        if unknown_documents:
            unknown = ", ".join(sorted(unknown_documents))
            raise DatasetValidationError(
                f"Question {question.id} references unknown documents: {unknown}"
            )
        seen_ids.add(question.id)
        questions.append(question)

    if not questions:
        raise DatasetValidationError("Evaluation dataset contains no questions")
    return EvaluationDataset(
        version=metadata.version,
        name=metadata.name,
        questions=questions,
    )


def compute_corpus_fingerprint(corpus_path: Path) -> str:
    digest = hashlib.sha256()
    supported = {".txt", ".md", ".markdown"}
    for path in sorted(corpus_path.iterdir()):
        if path.is_file() and path.suffix.lower() in supported:
            digest.update(path.name.encode())
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def compute_dataset_fingerprint(
    questions_path: Path, metadata_path: Path, corpus_path: Path
) -> str:
    digest = hashlib.sha256()
    supported = {".txt", ".md", ".markdown"}
    corpus_files = sorted(
        path
        for path in corpus_path.iterdir()
        if path.is_file() and path.suffix.lower() in supported
    )
    for path in [metadata_path, questions_path, *corpus_files]:
        digest.update(path.name.encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()
