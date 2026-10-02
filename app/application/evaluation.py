"""Offline retrieval evaluation utilities."""

from collections.abc import Callable
from dataclasses import dataclass
from statistics import mean

from app.application.retrieval import RetrievalService
from app.domain.entities import RetrievedChunk


@dataclass(frozen=True)
class RetrievalExample:
    """One query and the chunk identifiers considered relevant."""

    query: str
    relevant_chunk_ids: frozenset[str]


@dataclass(frozen=True)
class RetrievalEvaluation:
    """Aggregate retrieval metrics for a small offline evaluation set."""

    examples: int
    hit_at_k: float
    mean_reciprocal_rank: float


class RetrievalEvaluator:
    """Evaluate retrieval ranking without calling an LLM."""

    def __init__(
        self,
        retrieval_service: RetrievalService,
        search: Callable[..., list[RetrievedChunk]] | None = None,
    ) -> None:
        self._retrieval_service = retrieval_service
        self._search = search or retrieval_service.search

    def evaluate(
        self,
        examples: list[RetrievalExample],
        k: int = 4,
    ) -> RetrievalEvaluation:
        """Calculate Hit@K and MRR for the supplied examples."""

        if k < 1:
            raise ValueError("k must be at least 1")
        if not examples:
            return RetrievalEvaluation(0, 0.0, 0.0)

        hits: list[float] = []
        reciprocal_ranks: list[float] = []
        for example in examples:
            results = self._search(example.query, limit=k, min_score=0.0)
            ranked_ids = [result.chunk.chunk_id for result in results]
            relevant = example.relevant_chunk_ids
            hit_position = next(
                (
                    index
                    for index, chunk_id in enumerate(ranked_ids, start=1)
                    if chunk_id in relevant
                ),
                None,
            )
            hits.append(1.0 if hit_position is not None else 0.0)
            reciprocal_ranks.append(1.0 / hit_position if hit_position else 0.0)

        return RetrievalEvaluation(
            examples=len(examples),
            hit_at_k=mean(hits),
            mean_reciprocal_rank=mean(reciprocal_ranks),
        )
