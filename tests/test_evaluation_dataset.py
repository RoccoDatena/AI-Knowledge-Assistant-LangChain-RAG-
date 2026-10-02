"""Tests for the JSON retrieval evaluation dataset loader."""

import json
from pathlib import Path

import pytest

from app.application.evaluation_dataset import load_retrieval_examples


def test_loader_reads_versioned_json_examples(tmp_path: Path) -> None:
    dataset = tmp_path / "examples.json"
    dataset.write_text(
        json.dumps([{"query": "domanda", "relevant_chunk_ids": ["chunk:0"]}]),
        encoding="utf-8",
    )

    examples = load_retrieval_examples(dataset)

    assert examples[0].query == "domanda"
    assert examples[0].relevant_chunk_ids == frozenset({"chunk:0"})


def test_loader_rejects_invalid_dataset_shape(tmp_path: Path) -> None:
    dataset = tmp_path / "invalid.json"
    dataset.write_text(json.dumps({"query": "not-an-array"}), encoding="utf-8")

    with pytest.raises(ValueError, match="JSON array"):
        load_retrieval_examples(dataset)
