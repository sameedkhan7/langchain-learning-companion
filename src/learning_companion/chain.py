from functools import lru_cache

from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_xai import ChatXAI

from learning_companion.settings import get_settings

SYSTEM_INSTRUCTION = (
    "You are the Learning Companion, a friendly and patient study helper. "
    "Explain ideas clearly in plain language, use small examples, and keep "
    "answers short unless the learner asks for more detail."
)

# Counts earlier user and assistant messages, excluding the latest question.
MAX_HISTORY_MESSAGES = 6


class ConfigurationError(RuntimeError):
    """Raised when a model call is attempted without required settings."""


def build_prompt() -> ChatPromptTemplate:
    """System instruction, recent history, then the learner's current question."""
    return ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=SYSTEM_INSTRUCTION),
            MessagesPlaceholder("history", optional=True),
            ("human", "{question}"),
        ]
    )


def describe_prompt(question: str, history: list[BaseMessage]) -> list[str]:
    """Development aid: message roles in order, never any content."""
    messages = build_prompt().format_messages(question=question, history=history)
    return [message.type for message in messages]


@lru_cache
def get_chain():
    settings = get_settings()
    if not settings.grok_api_key:
        raise ConfigurationError("GROK_API_KEY is not set. Add it to your .env file.")
    if not settings.grok_model_name:
        raise ConfigurationError(
            "GROK_MODEL_NAME is not set. Add it to your .env file."
        )

    model = ChatXAI(
        model=settings.grok_model_name,
        api_key=settings.grok_api_key,
        xai_api_base=settings.grok_api_base_url,
    )
    return build_prompt() | model | StrOutputParser()
