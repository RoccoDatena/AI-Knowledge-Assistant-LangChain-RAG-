"""JSON persistence for uploaded document metadata."""

import json
from datetime import datetime
from pathlib import Path

from app.domain.entities import Document
from app.domain.ports import DocumentRepository
from app.infrastructure.persistence.atomic_file import atomic_write_text


class JsonDocumentRepository(DocumentRepository):
    """Store all document metadata in one JSON file."""

    def __init__(self, storage_path: Path) -> None:
        self._file_path = storage_path / "documents.json"
        self._file_path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, document: Document) -> Document:
        """Add or replace a document metadata record."""

        documents = self.list()
        documents = [
            item for item in documents if item.document_id != document.document_id
        ]
        documents.append(document)
        payload = [self._serialize(item) for item in documents]
        atomic_write_text(
            self._file_path, json.dumps(payload, indent=2, ensure_ascii=False)
        )
        return document

    def list(self) -> list[Document]:
        """Return metadata records, or an empty list when none exist."""

        if not self._file_path.is_file():
            return []
        payload = json.loads(self._file_path.read_text(encoding="utf-8"))
        return [self._deserialize(item) for item in payload]

    def delete(self, document_id: str) -> Document | None:
        """Delete a document record by ID."""

        documents = self.list()
        deleted = next(
            (document for document in documents if document.document_id == document_id),
            None,
        )
        if deleted is None:
            return None

        remaining = [
            document for document in documents if document.document_id != document_id
        ]
        atomic_write_text(
            self._file_path,
            json.dumps([self._serialize(item) for item in remaining], indent=2),
        )
        return deleted

    @staticmethod
    def _serialize(document: Document) -> dict[str, str | int]:
        return {
            "document_id": document.document_id,
            "filename": document.filename,
            "stored_path": document.stored_path,
            "uploaded_at": document.uploaded_at.isoformat(),
            "page_count": document.page_count,
            "text_length": document.text_length,
            "document_hash": document.document_hash,
        }

    @staticmethod
    def _deserialize(payload: dict[str, str | int]) -> Document:
        return Document(
            document_id=str(payload["document_id"]),
            filename=str(payload["filename"]),
            stored_path=str(payload["stored_path"]),
            uploaded_at=datetime.fromisoformat(str(payload["uploaded_at"])),
            page_count=int(payload["page_count"]),
            text_length=int(payload["text_length"]),
            document_hash=str(payload.get("document_hash", "")),
        )
