"""LangChain-based prompt construction kept outside the domain layer."""

from datetime import UTC, datetime

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.domain.entities import Message


class ConversationPromptBuilder:
    """Build a provider-neutral chat prompt."""

    _template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Sei un assistente utile. Rispondi in italiano, mantieni il contesto "
                "della conversazione e non inventare informazioni.",
            ),
            MessagesPlaceholder(variable_name="history"),
        ]
    )

    def build(self, messages: list[Message]) -> list[Message]:
        """Return domain messages after LangChain prompt formatting."""

        formatted_messages = self._template.format_messages(
            history=[self._to_langchain_message(message) for message in messages]
        )
        return [self._to_domain_message(message) for message in formatted_messages]

    @staticmethod
    def _to_langchain_message(message: Message) -> BaseMessage:
        if message.role == "user":
            return HumanMessage(content=message.content)
        if message.role == "assistant":
            return AIMessage(content=message.content)
        return SystemMessage(content=message.content)

    @staticmethod
    def _to_domain_message(message: BaseMessage) -> Message:
        role_by_type = {"human": "user", "ai": "assistant", "system": "system"}
        return Message(
            role=role_by_type.get(message.type, "system"),
            content=str(message.content),
            created_at=datetime.now(UTC),
        )
