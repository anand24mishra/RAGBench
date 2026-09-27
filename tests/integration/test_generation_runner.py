import json
from pathlib import Path

import pytest

from evaluation.generation_runner import (
    GenerationEvaluationConfig,
    run_generation_evaluation,
    write_generation_report,
)
from tests.fakes import FakeLLMProvider

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.mark.asyncio
async def test_generation_evaluation_end_to_end_fake_llm(tmp_path: Path) -> None:
    result_path = tmp_path / "gen_eval.json"
    summary_path = tmp_path / "gen_eval.md"

    # Small mock corpus and dataset
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    (corpus_dir / "ingestion.md").write_text(
        "RAGBench V1 accepts UTF-8 plain-text and Markdown files.", encoding="utf-8"
    )

    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "version": "1.1.0",
                "name": "test-dataset",
                "document_ids": ["ingestion"],
            }
        ),
        encoding="utf-8",
    )

    questions_path = tmp_path / "questions.jsonl"
    questions_path.write_text(
        json.dumps(
            {
                "id": "q001",
                "question": "What formats are accepted?",
                "relevant_documents": ["ingestion"],
                "reference_answer": "UTF-8 plain-text and Markdown files.",
                "required_facts": ["UTF-8 plain-text", "Markdown"],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    config = GenerationEvaluationConfig(
        experiment_id="test-gen-run",
        dataset_version="1.1.0",
        questions_path=questions_path,
        dataset_metadata_path=metadata_path,
        corpus_path=corpus_dir,
        result_path=result_path,
        summary_path=summary_path,
        chunk_size=400,
        chunk_overlap=50,
        top_k=2,
    )

    # Use FakeLLMProvider returning exact expected answer
    fake_llm = FakeLLMProvider(answer="RAGBench V1 accepts UTF-8 plain-text and Markdown files.")

    result = await run_generation_evaluation(config, llm_provider=fake_llm)

    assert result.experiment_id == "test-gen-run"
    assert result.schema_version == "4"
    assert result.query_count == 1
    assert "correctness" in result.metrics
    assert "faithfulness" in result.metrics
    assert "context_relevance" in result.metrics

    assert result.metrics["correctness"] == 1.0
    assert result.metrics["faithfulness"] == 1.0
    assert result.metrics["context_relevance"] == 1.0
    assert len(result.generation_failures) == 0

    assert result.timing is not None
    assert result.timing.generation_latency is not None

    write_generation_report(result, result_path, summary_path)

    assert result_path.exists()
    assert summary_path.exists()

    saved_json = json.loads(result_path.read_text(encoding="utf-8"))
    assert saved_json["schema_version"] == "4"
    assert saved_json["metrics"]["correctness"] == 1.0

    saved_md = summary_path.read_text(encoding="utf-8")
    assert "Generation Quality Evaluation: `test-gen-run`" in saved_md
    assert "Correctness" in saved_md
    assert "Faithfulness" in saved_md
