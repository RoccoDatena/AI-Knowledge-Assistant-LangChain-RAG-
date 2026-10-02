"""Tests for deterministic retrieval evaluation corpora."""

from pathlib import Path

import pytest

from app.application.evaluation_corpus import load_evaluation_corpus


def test_load_evaluation_corpus_preserves_chunk_metadata(tmp_path: Path) -> None:
    path = tmp_path / "corpus.json"
    path.write_text(
        '[{"chunk_id":"doc:0","document_id":"doc","content":"Testo",'
        '"page_number":2,"chunk_index":0}]',
        encoding="utf-8",
    )

    chunks = load_evaluation_corpus(path)

    assert len(chunks) == 1
    assert chunks[0].chunk_id == "doc:0"
    assert chunks[0].page_number == 2


def test_load_evaluation_corpus_rejects_missing_fields(tmp_path: Path) -> None:
    path = tmp_path / "corpus.json"
    path.write_text('[{"chunk_id":"doc:0"}]', encoding="utf-8")

    with pytest.raises(ValueError, match="missing required fields"):
        load_evaluation_corpus(path)
