from functools import lru_cache
from typing import Literal

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_xai import ChatXAI
from pydantic import BaseModel, Field

from learning_companion.chain import ConfigurationError
from learning_companion.settings import get_settings

REVIEW_SYSTEM_INSTRUCTION = (
    "You are a small answer reviewer. Approve the draft if it is clear, correct "
    "enough for a beginner, short, and fits the role: for the general route a "
    "friendly everyday reply; for the study route a plain-language explanation "
    "with one small example if useful and exactly one next learning step. "
    "Otherwise choose improve. Give one short plain-English reason."
)

IMPROVE_SYSTEM_INSTRUCTION = (
    "You are a small answer improver. Rewrite the draft once, following the "
    "reviewer's reason. Keep the same role and meaning. Return only the "
    "rewritten answer. You are a language model only: do not claim to research, "
    "browse, or use tools."
)


class ReviewResult(BaseModel):
    decision: Literal["approve", "improve"]
    reason: str = Field(description="One short plain-English sentence.")


def _model() -> ChatXAI:
    settings = get_settings()
    if not settings.grok_api_key:
        raise ConfigurationError("GROK_API_KEY is not set. Add it to your .env file.")
    if not settings.grok_model_name:
        raise ConfigurationError(
            "GROK_MODEL_NAME is not set. Add it to your .env file."
        )
    return ChatXAI(
        model=settings.grok_model_name,
        api_key=settings.grok_api_key,
        xai_api_base=settings.grok_api_base_url,
    )


@lru_cache
def get_review_chain():
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", REVIEW_SYSTEM_INSTRUCTION),
            (
                "human",
                "Route: {route}\n\nQuestion: {question}\n\nDraft answer:\n{draft}",
            ),
        ]
    )
    return prompt | _model().with_structured_output(ReviewResult)


@lru_cache
def get_improve_chain():
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", IMPROVE_SYSTEM_INSTRUCTION),
            (
                "human",
                "Route: {route}\n\nDraft answer:\n{draft}\n\nReviewer reason: {reason}",
            ),
        ]
    )
    return prompt | _model() | StrOutputParser()
