import json
from pathlib import Path

import pytest

from evaluation.dataset import DatasetValidationError, load_dataset


def write_metadata(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "version": "test-v1",
                "name": "test-dataset",
                "document_ids": ["doc-a", "doc-b"],
            }
        ),
        encoding="utf-8",
    )


def test_dataset_loads_valid_jsonl(tmp_path: Path) -> None:
    metadata = tmp_path / "metadata.json"
    questions = tmp_path / "questions.jsonl"
    write_metadata(metadata)
    questions.write_text(
        json.dumps(
            {
                "id": "q001",
                "question": "Where is alpha?",
                "relevant_documents": ["doc-a"],
                "reference_answer": "Alpha is in document A.",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    dataset = load_dataset(questions, metadata)

    assert dataset.version == "test-v1"
    assert dataset.questions[0].id == "q001"
    assert dataset.questions[0].reference_answer == "Alpha is in document A."


@pytest.mark.parametrize(
    "record",
    [
        "not json",
        json.dumps({"id": "q001", "question": "Missing labels"}),
        json.dumps(
            {
                "id": "q001",
                "question": "Blank relevance ID",
                "relevant_documents": [""],
            }
        ),
        json.dumps(
            {
                "id": "q001",
                "question": "Duplicate relevance IDs",
                "relevant_documents": ["doc-a", "doc-a"],
            }
        ),
    ],
)
def test_malformed_evaluation_record_is_rejected(tmp_path: Path, record: str) -> None:
    metadata = tmp_path / "metadata.json"
    questions = tmp_path / "questions.jsonl"
    write_metadata(metadata)
    questions.write_text(record + "\n", encoding="utf-8")

    with pytest.raises(DatasetValidationError, match="Invalid evaluation record"):
        load_dataset(questions, metadata)


def test_unknown_relevant_document_is_rejected(tmp_path: Path) -> None:
    metadata = tmp_path / "metadata.json"
    questions = tmp_path / "questions.jsonl"
    write_metadata(metadata)
    questions.write_text(
        json.dumps(
            {
                "id": "q001",
                "question": "Unknown document",
                "relevant_documents": ["doc-missing"],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(DatasetValidationError, match="unknown documents"):
        load_dataset(questions, metadata)


def test_duplicate_question_id_is_rejected(tmp_path: Path) -> None:
    metadata = tmp_path / "metadata.json"
    questions = tmp_path / "questions.jsonl"
    write_metadata(metadata)
    record = json.dumps(
        {
            "id": "q001",
            "question": "Question",
            "relevant_documents": ["doc-a"],
        }
    )
    questions.write_text(f"{record}\n{record}\n", encoding="utf-8")

    with pytest.raises(DatasetValidationError, match="Duplicate evaluation question ID"):
        load_dataset(questions, metadata)
