"""Ports required by the application layer."""

from typing import Protocol

from app.domain.entities import (
    Conversation,
    Document,
    DocumentChunk,
    Message,
    RetrievedChunk,
)


class ConversationRepository(Protocol):
    """Persistence contract for conversations."""

    def create(self) -> Conversation:
        """Create and persist a new empty conversation."""

    def get(self, conversation_id: str) -> Conversation | None:
        """Return a conversation or ``None`` when it does not exist."""

    def add_message(
        self, conversation_id: str, message: Message
    ) -> Conversation | None:
        """Append a message and return the updated conversation."""


class DocumentRepository(Protocol):
    """Persistence contract for uploaded document metadata."""

    def save(self, document: Document) -> Document:
        """Persist document metadata."""

    def list(self) -> list[Document]:
        """Return all uploaded documents."""

    def delete(self, document_id: str) -> Document | None:
        """Delete and return document metadata."""


class EmbeddingProvider(Protocol):
    """Contract for document and query embedding providers."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Create one vector for every input text."""

    def embed_query(self, text: str) -> list[float]:
        """Create a vector for a search query."""


class VectorStore(Protocol):
    """Contract for persistent or in-memory vector stores."""

    def add(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> None:
        """Store chunks and their vectors."""

    def search(
        self,
        query_embedding: list[float],
        limit: int = 4,
        metadata_filter: dict[str, str] | None = None,
    ) -> list[RetrievedChunk]:
        """Return the most relevant chunks."""

    def delete_by_document_id(self, document_id: str) -> int:
        """Delete vectors belonging to a document and return the count."""


class LLMProvider(Protocol):
    """Contract for conversational model adapters."""

    def generate(self, messages: list[Message]) -> str:
        """Generate an answer from the conversation context."""
