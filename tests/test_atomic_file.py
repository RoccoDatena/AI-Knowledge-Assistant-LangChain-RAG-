"""Tests for atomic persistence helpers."""

from pathlib import Path

from app.infrastructure.persistence.atomic_file import atomic_write_text


def test_atomic_write_replaces_file_without_temporary_artifacts(tmp_path: Path) -> None:
    target = tmp_path / "state.json"

    atomic_write_text(target, '{"status": "ready"}')

    assert target.read_text(encoding="utf-8") == '{"status": "ready"}'
    assert list(tmp_path.glob(".state.json.*.tmp")) == []
