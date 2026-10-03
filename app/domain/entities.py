"""Core conversation entities."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class MessageSource:
    """Persisted source metadata attached to an assistant response."""

    document_id: str
    filename: str
    page_number: int
    chunk_id: str
    score: float


@dataclass(frozen=True)
class Message:
    """A message exchanged in a conversation."""

    role: str
    content: str
    created_at: datetime
    grounded: bool | None = None
    sources: list[MessageSource] = field(default_factory=list)


@dataclass
class Conversation:
    """Conversation aggregate persisted by a repository implementation."""

    conversation_id: str
    created_at: datetime
    messages: list[Message] = field(default_factory=list)


@dataclass(frozen=True)
class Document:
    """Metadata for an uploaded PDF document."""

    document_id: str
    filename: str
    stored_path: str
    uploaded_at: datetime
    page_count: int
    text_length: int
    document_hash: str = ""


@dataclass(frozen=True)
class DocumentChunk:
    """A retrievable text fragment with source metadata."""

    chunk_id: str
    document_id: str
    content: str
    page_number: int
    chunk_index: int
    document_hash: str
    filename: str = ""


@dataclass(frozen=True)
class RetrievedChunk:
    """A chunk returned by similarity search with its relevance score."""

    chunk: DocumentChunk
    score: float
