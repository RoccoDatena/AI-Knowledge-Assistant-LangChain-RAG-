"""Tests for offline retrieval metrics."""

import pytest

from app.application.evaluation import RetrievalEvaluator, RetrievalExample
from app.domain.entities import DocumentChunk, RetrievedChunk


class FakeRetrieval:
    def search(self, query: str, limit: int, min_score: float) -> list[RetrievedChunk]:
        del query, limit, min_score
        return [
            RetrievedChunk(
                DocumentChunk(
                    chunk_id="relevant",
                    document_id="doc",
                    content="content",
                    page_number=1,
                    chunk_index=0,
                    document_hash="hash",
                    filename="doc.pdf",
                ),
                0.9,
            ),
            RetrievedChunk(
                DocumentChunk(
                    chunk_id="other",
                    document_id="doc",
                    content="other",
                    page_number=1,
                    chunk_index=1,
                    document_hash="hash",
                    filename="doc.pdf",
                ),
                0.2,
            ),
        ]


def test_evaluator_calculates_hit_at_k_and_mrr() -> None:
    evaluator = RetrievalEvaluator(FakeRetrieval())  # type: ignore[arg-type]
    result = evaluator.evaluate(
        [RetrievalExample("question", frozenset({"relevant"}))], k=2
    )

    assert result.examples == 1
    assert result.hit_at_k == 1.0
    assert result.mean_reciprocal_rank == 1.0


def test_evaluator_rejects_invalid_k() -> None:
    evaluator = RetrievalEvaluator(FakeRetrieval())  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="at least 1"):
        evaluator.evaluate([], k=0)
