"""Grounded retrieval-augmented generation use case."""

from dataclasses import dataclass
from datetime import UTC

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.application.retrieval import RetrievalService
from app.domain.entities import Message, RetrievedChunk
from app.domain.ports import LLMProvider

NOT_FOUND_ANSWER = "Informazione non trovata nei documenti."


@dataclass(frozen=True)
class Citation:
    """Source citation generated from retrieved metadata."""

    document_id: str
    filename: str
    page_number: int
    chunk_id: str
    score: float


@dataclass(frozen=True)
class RagAnswer:
    """Grounded answer and its source citations."""

    answer: str
    citations: list[Citation]
    grounded: bool


class RagPromptBuilder:
    """Build a prompt that constrains generation to retrieved context."""

    _template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Rispondi esclusivamente usando il contesto documentale fornito. "
                "Se il contesto non contiene la risposta, non fare supposizioni. "
                "Rispondi in italiano.\n\nContesto:\n{context}",
            ),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    )

    def build(
        self,
        question: str,
        history: list[Message],
        retrieved_chunks: list[RetrievedChunk],
    ) -> list[Message]:
        """Format history and retrieved chunks into domain messages."""

        context = "\n\n".join(
            f"[Fonte: {result.chunk.filename}, pagina {result.chunk.page_number}]\n"
            f"{result.chunk.content}"
            for result in retrieved_chunks
        )
        formatted = self._template.format_messages(
            context=context,
            history=[self._to_langchain(message) for message in history],
            question=question,
        )
        return [self._to_domain(message) for message in formatted]

    @staticmethod
    def _to_langchain(message: Message) -> BaseMessage:
        if message.role == "user":
            return HumanMessage(content=message.content)
        if message.role == "assistant":
            return AIMessage(content=message.content)
        return SystemMessage(content=message.content)

    @staticmethod
    def _to_domain(message: BaseMessage) -> Message:
        role_by_type = {"human": "user", "ai": "assistant", "system": "system"}
        from datetime import datetime

        return Message(
            role=role_by_type.get(message.type, "system"),
            content=str(message.content),
            created_at=datetime.now(UTC),
        )


class RagService:
    """Retrieve context and call an LLM only when evidence exists."""

    def __init__(
        self,
        retrieval_service: RetrievalService,
        llm_provider: LLMProvider,
        prompt_builder: RagPromptBuilder,
        min_score: float = 0.15,
    ) -> None:
        self._retrieval_service = retrieval_service
        self._llm_provider = llm_provider
        self._prompt_builder = prompt_builder
        self._min_score = min_score

    def answer(self, question: str, history: list[Message]) -> RagAnswer:
        """Return a grounded answer or the standard not-found response."""

        retrieved = self._retrieval_service.search(
            question,
            limit=4,
            min_score=self._min_score,
        )
        citations = [
            Citation(
                document_id=result.chunk.document_id,
                filename=result.chunk.filename,
                page_number=result.chunk.page_number,
                chunk_id=result.chunk.chunk_id,
                score=result.score,
            )
            for result in retrieved
        ]
        if not retrieved:
            return RagAnswer(NOT_FOUND_ANSWER, [], False)

        prompt_messages = self._prompt_builder.build(question, history, retrieved)
        return RagAnswer(self._llm_provider.generate(prompt_messages), citations, True)
