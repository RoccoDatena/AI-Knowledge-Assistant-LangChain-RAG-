"""Conversation HTTP endpoints."""

from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.application.prompt_builder import ConversationPromptBuilder
from app.application.rag import RagService
from app.application.retrieval import RetrievalService
from app.core.config import get_settings
from app.domain.entities import Message, MessageSource
from app.domain.ports import ConversationRepository, LLMProvider
from app.infrastructure.llm.mock_llm import MockLLM
from app.infrastructure.llm.openrouter_adapter import OpenRouterAdapter
from app.infrastructure.persistence.json_conversation_repository import (
    JsonConversationRepository,
)
from app.interfaces.api.search_routes import get_retrieval_service


class ConversationResponse(BaseModel):
    """Public representation of a conversation."""

    conversation_id: str
    created_at: str
    message_count: int


class HistoryMessageResponse(BaseModel):
    """Public representation of a persisted conversation message."""

    role: str
    content: str
    created_at: str
    grounded: bool | None = None
    sources: list[dict[str, str | int | float]] = Field(default_factory=list)


class ConversationHistoryResponse(ConversationResponse):
    """Public representation including conversation messages."""

    messages: list[HistoryMessageResponse]


class SendMessageRequest(BaseModel):
    """Payload accepted when a user sends a message."""

    content: str = Field(min_length=1, max_length=4000)


class MessageResponse(BaseModel):
    """Message returned by the chat endpoint."""

    role: str
    content: str
    created_at: str


class SendMessageResponse(BaseModel):
    """Assistant response together with the persisted user message."""

    conversation_id: str
    user_message: MessageResponse
    assistant_message: MessageResponse
    grounded: bool
    sources: list[dict[str, str | int | float]]


router = APIRouter(prefix="/conversations", tags=["conversations"])


def get_conversation_repository() -> ConversationRepository:
    """Build the JSON adapter used by the current application configuration."""

    return JsonConversationRepository(
        Path(get_settings().data_directory) / "conversations"
    )


def get_llm_provider() -> LLMProvider:
    """Build the local provider used until a remote adapter is configured."""

    settings = get_settings()
    if settings.llm_provider == "openrouter":
        return OpenRouterAdapter(settings)
    return MockLLM()


def get_prompt_builder() -> ConversationPromptBuilder:
    """Build the LangChain prompt formatter."""

    return ConversationPromptBuilder()


def get_rag_service(
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
    llm_provider: LLMProvider = Depends(get_llm_provider),
) -> RagService:
    """Build the grounded answer service."""

    from app.application.rag import RagPromptBuilder

    return RagService(
        retrieval_service,
        llm_provider,
        RagPromptBuilder(),
        min_score=get_settings().rag_min_score,
        require_lexical_evidence=get_settings().rag_require_lexical_evidence,
    )


@router.post("", response_model=ConversationResponse, status_code=201)
def create_conversation(
    repository: ConversationRepository = Depends(get_conversation_repository),
) -> ConversationResponse:
    """Create an empty conversation."""

    conversation = repository.create()
    return ConversationResponse(
        conversation_id=conversation.conversation_id,
        created_at=conversation.created_at.isoformat(),
        message_count=len(conversation.messages),
    )


@router.get("/{conversation_id}/history", response_model=ConversationHistoryResponse)
def get_conversation_history(
    conversation_id: str,
    repository: ConversationRepository = Depends(get_conversation_repository),
) -> ConversationHistoryResponse:
    """Return the messages belonging to a conversation."""

    conversation = repository.get(conversation_id)
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return ConversationHistoryResponse(
        conversation_id=conversation.conversation_id,
        created_at=conversation.created_at.isoformat(),
        message_count=len(conversation.messages),
        messages=[
            HistoryMessageResponse(
                role=message.role,
                content=message.content,
                created_at=message.created_at.isoformat(),
                grounded=message.grounded,
                sources=[
                    {
                        "document_id": source.document_id,
                        "filename": source.filename,
                        "page_number": source.page_number,
                        "chunk_id": source.chunk_id,
                        "score": source.score,
                    }
                    for source in message.sources
                ],
            )
            for message in conversation.messages
        ],
    )


@router.post(
    "/{conversation_id}/messages",
    response_model=SendMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    repository: ConversationRepository = Depends(get_conversation_repository),
    llm_provider: LLMProvider = Depends(get_llm_provider),
    prompt_builder: ConversationPromptBuilder = Depends(get_prompt_builder),
    rag_service: RagService = Depends(get_rag_service),
) -> SendMessageResponse:
    """Persist a user message, generate an answer, and persist the answer."""

    conversation = repository.get(conversation_id)
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    user_message = Message(
        role="user",
        content=request.content,
        created_at=datetime.now(UTC),
    )
    updated_conversation = repository.add_message(conversation_id, user_message)
    if updated_conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    rag_answer = rag_service.answer(
        question=user_message.content,
        history=updated_conversation.messages[:-1],
    )
    assistant_message = Message(
        role="assistant",
        content=rag_answer.answer,
        created_at=datetime.now(UTC),
        grounded=rag_answer.grounded,
        sources=[
            MessageSource(
                document_id=citation.document_id,
                filename=citation.filename,
                page_number=citation.page_number,
                chunk_id=citation.chunk_id,
                score=citation.score,
            )
            for citation in rag_answer.citations
        ],
    )
    repository.add_message(conversation_id, assistant_message)

    return SendMessageResponse(
        conversation_id=conversation_id,
        user_message=MessageResponse(
            role=user_message.role,
            content=user_message.content,
            created_at=user_message.created_at.isoformat(),
        ),
        assistant_message=MessageResponse(
            role=assistant_message.role,
            content=assistant_message.content,
            created_at=assistant_message.created_at.isoformat(),
        ),
        grounded=rag_answer.grounded,
        sources=[
            {
                "document_id": citation.document_id,
                "filename": citation.filename,
                "page_number": citation.page_number,
                "chunk_id": citation.chunk_id,
                "score": citation.score,
            }
            for citation in rag_answer.citations
        ],
    )
