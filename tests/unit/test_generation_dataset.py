import json
from pathlib import Path

import pytest

from evaluation.dataset import (
    EvaluationQuestion,
    compute_corpus_fingerprint,
    compute_dataset_fingerprint,
    load_dataset,
)


def write_test_metadata(path: Path, version: str = "1.1.0") -> None:
    path.write_text(
        json.dumps(
            {
                "version": version,
                "name": "test-generation-dataset",
                "document_ids": ["doc_01", "doc_02"],
            }
        ),
        encoding="utf-8",
    )


def test_valid_generation_record_with_required_facts(tmp_path: Path) -> None:
    metadata = tmp_path / "metadata.json"
    questions = tmp_path / "questions.jsonl"
    write_test_metadata(metadata)

    record = {
        "id": "q001",
        "question": "What formats are supported?",
        "relevant_documents": ["doc_01"],
        "reference_answer": "Plain text and Markdown.",
        "required_facts": ["Plain text", "Markdown"],
    }
    questions.write_text(json.dumps(record) + "\n", encoding="utf-8")

    ds = load_dataset(questions, metadata)
    assert len(ds.questions) == 1
    assert ds.version == "1.1.0"
    q = ds.questions[0]
    assert q.id == "q001"
    assert q.required_facts == ["Plain text", "Markdown"]
    assert q.reference_answer == "Plain text and Markdown."


def test_generation_record_optional_reference_answer(tmp_path: Path) -> None:
    metadata = tmp_path / "metadata.json"
    questions = tmp_path / "questions.jsonl"
    write_test_metadata(metadata)

    record = {
        "id": "q002",
        "question": "Where is doc_02?",
        "relevant_documents": ["doc_02"],
    }
    questions.write_text(json.dumps(record) + "\n", encoding="utf-8")

    ds = load_dataset(questions, metadata)
    q = ds.questions[0]
    assert q.reference_answer is None
    assert q.required_facts == []


def test_malformed_required_facts_blank_string() -> None:
    with pytest.raises(ValueError, match="required facts must not contain blank text"):
        EvaluationQuestion(
            id="q_bad",
            question="Valid question text?",
            relevant_documents=["doc_01"],
            required_facts=["Valid fact", "   "],
        )


def test_malformed_required_facts_empty_list_is_allowed() -> None:
    q = EvaluationQuestion(
        id="q_ok",
        question="Valid question text?",
        relevant_documents=["doc_01"],
        required_facts=[],
    )
    assert q.required_facts == []


def test_dataset_version_validation(tmp_path: Path) -> None:
    metadata = tmp_path / "metadata.json"
    questions = tmp_path / "questions.jsonl"
    write_test_metadata(metadata, version="2.0.0")

    record = {
        "id": "q1",
        "question": "Test question?",
        "relevant_documents": ["doc_01"],
    }
    questions.write_text(json.dumps(record) + "\n", encoding="utf-8")

    ds = load_dataset(questions, metadata)
    assert ds.version == "2.0.0"


def test_fingerprint_computation(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    (corpus_dir / "doc_01.md").write_text("Hello doc 1", encoding="utf-8")
    (corpus_dir / "doc_02.txt").write_text("Hello doc 2", encoding="utf-8")

    metadata = tmp_path / "metadata.json"
    questions = tmp_path / "questions.jsonl"
    write_test_metadata(metadata)
    questions.write_text(
        json.dumps(
            {
                "id": "q1",
                "question": "Test?",
                "relevant_documents": ["doc_01"],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    corpus_fp = compute_corpus_fingerprint(corpus_dir)
    assert isinstance(corpus_fp, str)
    assert len(corpus_fp) == 64

    dataset_fp = compute_dataset_fingerprint(questions, metadata, corpus_dir)
    assert isinstance(dataset_fp, str)
    assert len(dataset_fp) == 64
    assert dataset_fp != corpus_fp
