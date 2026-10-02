"""Tests for grounded answer behavior and citations."""

from datetime import UTC, datetime

from app.application.rag import NOT_FOUND_ANSWER, RagPromptBuilder, RagService
from app.domain.entities import DocumentChunk, Message, RetrievedChunk


class FakeRetrieval:
    def __init__(self, results: list[RetrievedChunk]) -> None:
        self.results = results

    def search(self, *args, **kwargs) -> list[RetrievedChunk]:
        return self.results


class RecordingLLM:
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, messages: list[Message]) -> str:
        self.calls += 1
        assert any(message.role == "system" for message in messages)
        assert any("Manuale" in message.content for message in messages)
        return "Risposta grounded"


def test_rag_returns_standard_answer_without_context() -> None:
    """The LLM must not be called when retrieval finds no evidence."""

    llm = RecordingLLM()
    service = RagService(FakeRetrieval([]), llm, RagPromptBuilder())

    result = service.answer("Domanda senza evidenza", [])

    assert result.answer == NOT_FOUND_ANSWER
    assert result.grounded is False
    assert result.citations == []
    assert llm.calls == 0


def test_rag_returns_answer_and_backend_generated_citation() -> None:
    """Citations should come from chunk metadata, not generated text."""

    chunk = DocumentChunk(
        chunk_id="doc-1:0",
        document_id="doc-1",
        content="Il prodotto è disponibile.",
        page_number=3,
        chunk_index=0,
        document_hash="hash",
        filename="Manuale.pdf",
    )
    llm = RecordingLLM()
    service = RagService(
        FakeRetrieval([RetrievedChunk(chunk, 0.88)]), llm, RagPromptBuilder()
    )

    result = service.answer(
        "Dove è disponibile il prodotto?",
        [Message("user", "Ciao", datetime.now(UTC))],
    )

    assert result.answer == "Risposta grounded"
    assert result.grounded is True
    assert result.citations[0].filename == "Manuale.pdf"
    assert result.citations[0].page_number == 3
    assert llm.calls == 1
