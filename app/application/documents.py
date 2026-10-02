"""Document lifecycle use cases."""

from pathlib import Path

from app.domain.ports import DocumentRepository, VectorStore


class DeleteDocumentService:
    """Delete document metadata, binary content, and indexed vectors."""

    def __init__(
        self, repository: DocumentRepository, vector_store: VectorStore
    ) -> None:
        self._repository = repository
        self._vector_store = vector_store

    def delete(self, document_id: str) -> bool:
        """Delete all local document resources, returning whether it existed."""

        document = self._repository.delete(document_id)
        if document is None:
            return False
        Path(document.stored_path).unlink(missing_ok=True)
        self._vector_store.delete_by_document_id(document_id)
        return True
