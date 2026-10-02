"""Load deterministic chunk fixtures for offline retrieval evaluation."""

import json
from pathlib import Path
from typing import Any

from app.domain.entities import DocumentChunk


def load_evaluation_corpus(path: Path) -> list[DocumentChunk]:
    """Load and validate a JSON corpus of retrievable chunks."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Unable to load evaluation corpus: {path}") from exc
    if not isinstance(payload, list):
        raise ValueError("Evaluation corpus must be a JSON array")

    chunks: list[DocumentChunk] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"Corpus item {index} must be an object")
        chunks.append(_to_chunk(item, index))
    return chunks


def _to_chunk(item: dict[str, Any], index: int) -> DocumentChunk:
    """Convert one validated JSON object to a domain chunk."""

    required = ("chunk_id", "document_id", "content", "page_number", "chunk_index")
    if any(key not in item for key in required):
        raise ValueError(f"Corpus item {index} is missing required fields")
    text_fields_valid = all(
        isinstance(item[key], str) and item[key].strip() for key in required[:3]
    )
    if not text_fields_valid:
        raise ValueError(f"Corpus item {index} has invalid text fields")
    if not isinstance(item["page_number"], int) or item["page_number"] < 1:
        raise ValueError(f"Corpus item {index} has an invalid page_number")
    if not isinstance(item["chunk_index"], int) or item["chunk_index"] < 0:
        raise ValueError(f"Corpus item {index} has an invalid chunk_index")
    return DocumentChunk(
        chunk_id=item["chunk_id"],
        document_id=item["document_id"],
        content=item["content"],
        page_number=item["page_number"],
        chunk_index=item["chunk_index"],
        document_hash=str(item.get("document_hash", "evaluation-fixture")),
        filename=str(item.get("filename", "evaluation-fixture.pdf")),
    )
