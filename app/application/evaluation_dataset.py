"""Load and validate JSON datasets used for retrieval evaluation."""

import json
from pathlib import Path
from typing import Any

from app.application.evaluation import RetrievalExample


def load_retrieval_examples(path: Path) -> list[RetrievalExample]:
    """Load retrieval examples from a versioned JSON file."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Unable to load evaluation dataset: {path}") from exc
    if not isinstance(payload, list):
        raise ValueError("Evaluation dataset must be a JSON array")

    examples: list[RetrievalExample] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"Dataset item {index} must be an object")
        query = item.get("query")
        relevant_chunk_ids = item.get("relevant_chunk_ids")
        if not isinstance(query, str) or not query.strip():
            raise ValueError(f"Dataset item {index} has an invalid query")
        if not _is_string_list(relevant_chunk_ids) or not relevant_chunk_ids:
            raise ValueError(f"Dataset item {index} must contain relevant_chunk_ids")
        examples.append(RetrievalExample(query, frozenset(relevant_chunk_ids)))
    return examples


def _is_string_list(value: Any) -> bool:
    """Return whether a value is a list containing only strings."""

    return isinstance(value, list) and all(isinstance(item, str) for item in value)
