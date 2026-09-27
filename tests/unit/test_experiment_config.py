from pathlib import Path

import pytest

from ragbench.experiments.config import (
    ControlledExperimentError,
    ExperimentConfig,
    load_experiment_config,
    validate_controlled_experiment,
)


def test_valid_configuration(tmp_path: Path) -> None:
    config_file = tmp_path / "valid.yaml"
    config_file.write_text(
        """
experiment_id: test-valid
dataset_version: 1.0.0
chunk_size: 500
chunk_overlap: 50
top_k: 5
embedding_model: sentence-transformers/all-MiniLM-L6-v2
""",
        encoding="utf-8",
    )
    cfg = load_experiment_config(config_file)
    assert cfg.experiment_id == "test-valid"
    assert cfg.dataset_version == "1.0.0"
    assert cfg.chunk_size == 500
    assert cfg.chunk_overlap == 50
    assert cfg.top_k == 5
    assert cfg.embedding_batch_size == 32
    assert cfg.result_path.name == "test-valid.json"
    assert cfg.summary_path.name == "test-valid.md"


@pytest.mark.parametrize("chunk_size", [0, -100])
def test_invalid_chunk_size(chunk_size: int) -> None:
    with pytest.raises(ValueError):
        ExperimentConfig(
            experiment_id="test",
            dataset_version="1.0.0",
            chunk_size=chunk_size,
            chunk_overlap=0,
            top_k=5,
        )


def test_invalid_overlap_greater_than_or_equal_to_chunk_size() -> None:
    with pytest.raises(ValueError, match="chunk_overlap must be smaller than chunk_size"):
        ExperimentConfig(
            experiment_id="test",
            dataset_version="1.0.0",
            chunk_size=500,
            chunk_overlap=500,
            top_k=5,
        )

    with pytest.raises(ValueError, match="chunk_overlap must be smaller than chunk_size"):
        ExperimentConfig(
            experiment_id="test",
            dataset_version="1.0.0",
            chunk_size=500,
            chunk_overlap=600,
            top_k=5,
        )


def test_invalid_overlap_negative() -> None:
    with pytest.raises(ValueError):
        ExperimentConfig(
            experiment_id="test",
            dataset_version="1.0.0",
            chunk_size=500,
            chunk_overlap=-10,
            top_k=5,
        )


@pytest.mark.parametrize("top_k", [0, -5])
def test_invalid_top_k(top_k: int) -> None:
    with pytest.raises(ValueError):
        ExperimentConfig(
            experiment_id="test",
            dataset_version="1.0.0",
            chunk_size=500,
            chunk_overlap=50,
            top_k=top_k,
        )


def test_missing_dataset_version() -> None:
    with pytest.raises(ValueError):
        ExperimentConfig(
            experiment_id="test",
            dataset_version="",
            chunk_size=500,
            chunk_overlap=50,
            top_k=5,
        )


def test_missing_experiment_id() -> None:
    with pytest.raises(ValueError):
        ExperimentConfig(
            experiment_id="   ",
            dataset_version="1.0.0",
            chunk_size=500,
            chunk_overlap=50,
            top_k=5,
        )


def test_qdrant_mode_memory_enforced() -> None:
    with pytest.raises(ValueError, match="supports qdrant_mode=memory only"):
        ExperimentConfig(
            experiment_id="test",
            dataset_version="1.0.0",
            chunk_size=500,
            chunk_overlap=50,
            top_k=5,
            qdrant_mode="remote",
        )


def test_controlled_experiment_single_variable_allowed() -> None:
    baseline = ExperimentConfig(
        experiment_id="base",
        dataset_version="1.0.0",
        chunk_size=800,
        chunk_overlap=100,
        top_k=5,
        embedding_model="model-a",
    )
    chunking_exp = baseline.model_copy(update={"chunk_size": 400, "chunk_overlap": 50})
    topk_exp = baseline.model_copy(update={"top_k": 10})
    embed_exp = baseline.model_copy(update={"embedding_model": "model-b"})

    assert validate_controlled_experiment(baseline, chunking_exp) == ["chunking"]
    assert validate_controlled_experiment(baseline, topk_exp) == ["top_k"]
    assert validate_controlled_experiment(baseline, embed_exp) == ["embedding_model"]
    assert validate_controlled_experiment(baseline, baseline) == []


def test_controlled_experiment_multiple_variables_rejected() -> None:
    baseline = ExperimentConfig(
        experiment_id="base",
        dataset_version="1.0.0",
        chunk_size=800,
        chunk_overlap=100,
        top_k=5,
        embedding_model="model-a",
    )
    # Changing both chunking and top_k simultaneously
    bad_exp = baseline.model_copy(update={"chunk_size": 400, "chunk_overlap": 50, "top_k": 10})

    with pytest.raises(
        ControlledExperimentError, match="multiple variables changed simultaneously"
    ):
        validate_controlled_experiment(baseline, bad_exp)


def test_controlled_experiment_incompatible_dataset_version_rejected() -> None:
    baseline = ExperimentConfig(
        experiment_id="base",
        dataset_version="1.0.0",
        chunk_size=800,
        chunk_overlap=100,
        top_k=5,
    )
    diff_version = baseline.model_copy(update={"dataset_version": "2.0.0"})

    with pytest.raises(ControlledExperimentError, match="different dataset versions"):
        validate_controlled_experiment(baseline, diff_version)
