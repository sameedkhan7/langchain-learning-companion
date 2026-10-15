from functools import lru_cache

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_xai import ChatXAI

from learning_companion.settings import get_settings

SYSTEM_INSTRUCTION = (
    "You are the Learning Companion, a friendly and patient study helper. "
    "Explain ideas clearly in plain language, use small examples, and keep "
    "answers short unless the learner asks for more detail."
)


class ConfigurationError(RuntimeError):
    """Raised when a model call is attempted without required settings."""


@lru_cache
def get_chain():
    settings = get_settings()
    if not settings.grok_api_key:
        raise ConfigurationError("GROK_API_KEY is not set. Add it to your .env file.")
    if not settings.grok_model_name:
        raise ConfigurationError(
            "GROK_MODEL_NAME is not set. Add it to your .env file."
        )

    prompt = ChatPromptTemplate.from_messages(
        [("system", SYSTEM_INSTRUCTION), ("human", "{question}")]
    )
    model = ChatXAI(
        model=settings.grok_model_name,
        api_key=settings.grok_api_key,
        xai_api_base=settings.grok_api_base_url,
    )
    return prompt | model | StrOutputParser()
