import json
import logging
import time
import uuid
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from pydantic import BaseModel

from learning_companion.chain import (
    MAX_HISTORY_MESSAGES,
    ConfigurationError,
    describe_prompt,
    get_chain,
    get_study_chain,
)
from learning_companion.settings import get_settings

logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="Learning Companion Chatbot")


class Message(BaseModel):
    role: str
    content: str | list[Any] | None = None


class ChatRequest(BaseModel):
    model: str = ""
    messages: list[Message]
    stream: bool = False


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/v1/models")
def list_models():
    name = get_settings().grok_model_name
    data = (
        [{"id": name, "object": "model", "created": 0, "owned_by": "xai"}]
        if name
        else []
    )
    return {"object": "list", "data": data}


def _text_of(message: Message) -> str:
    """Plain text of a message; list-style content keeps only its text parts."""
    content = message.content
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = [
            part.get("text", "")
            for part in content
            if isinstance(part, dict)
            and part.get("type") == "text"
            and isinstance(part.get("text"), str)
        ]
        return "".join(parts).strip()
    return ""


def _build_history(messages: list[Message]) -> tuple[str, list[BaseMessage]]:
    """Latest user question plus the recent user/assistant messages before it."""
    supported = [
        (message.role, text)
        for message in messages
        if message.role in ("user", "assistant") and (text := _text_of(message))
    ]
    for index in range(len(supported) - 1, -1, -1):
        if supported[index][0] == "user":
            question = supported[index][1]
            earlier = supported[:index][-MAX_HISTORY_MESSAGES:]
            history = [
                HumanMessage(content=text)
                if role == "user"
                else AIMessage(content=text)
                for role, text in earlier
            ]
            return question, history
    return "", []


STUDY_MARKER = "/study"
STUDY_FALLBACK_QUESTION = "What should I study first as a beginner?"


def _choose_route(question: str) -> tuple[str, str]:
    """Plain rule: a leading '/study' picks the study chain, else general."""
    after = question[len(STUDY_MARKER) :]
    if question.startswith(STUDY_MARKER) and (not after or after[0].isspace()):
        rest = question[len(STUDY_MARKER) :].strip()
        return "study", rest or STUDY_FALLBACK_QUESTION
    return "general", question


def _sse(payload: dict | str) -> str:
    body = payload if isinstance(payload, str) else json.dumps(payload)
    return f"data: {body}\n\n"


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    question, history = _build_history(request.messages)
    route, question = _choose_route(question)
    try:
        chain = get_study_chain() if route == "study" else get_chain()
    except ConfigurationError as error:
        return JSONResponse(status_code=503, content={"error": {"message": str(error)}})

    label = f"[route: {route}]\n\n"
    if get_settings().app_env == "development":
        roles = describe_prompt(question, history, study=route == "study")
        logger.info(
            "route: %s; prompt: %s — %d messages; request system message set aside: %s",
            route,
            ", ".join(roles),
            len(roles),
            any(m.role == "system" for m in request.messages),
        )
    completion_id = f"chatcmpl-{uuid.uuid4().hex}"
    created = int(time.time())
    model = request.model or get_settings().grok_model_name

    if not request.stream:
        text = await chain.ainvoke({"question": question, "history": history})
        return {
            "id": completion_id,
            "object": "chat.completion",
            "created": created,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": label + text},
                    "finish_reason": "stop",
                }
            ],
        }

    def chunk(delta: dict, finish_reason: str | None = None) -> dict:
        return {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}],
        }

    async def event_stream():
        yield _sse(chunk({"content": label}))
        try:
            async for piece in chain.astream(
                {"question": question, "history": history}
            ):
                if piece:
                    yield _sse(chunk({"content": piece}))
        except Exception as error:  # noqa: BLE001 - surface upstream failures in-stream
            yield _sse({"error": {"message": str(error)}})
        yield _sse(chunk({}, "stop"))
        yield _sse("[DONE]")

    return StreamingResponse(event_stream(), media_type="text/event-stream")
