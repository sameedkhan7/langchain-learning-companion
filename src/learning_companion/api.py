import json
import logging
import time
import uuid
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from pydantic import BaseModel

from learning_companion.chain import MAX_HISTORY_MESSAGES, ConfigurationError, get_chain
from learning_companion.graph import build_graph
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


def _sse(payload: dict | str) -> str:
    body = payload if isinstance(payload, str) else json.dumps(payload)
    return f"data: {body}\n\n"


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    question, history = _build_history(request.messages)
    try:
        get_chain()  # fail early with 503 if Grok settings are missing
    except ConfigurationError as error:
        return JSONResponse(status_code=503, content={"error": {"message": str(error)}})

    graph = build_graph()
    state = {
        "user_message": question,
        "messages": history,
        "route": "",
        "draft_answer": "",
        "review_decision": "",
        "review_reason": "",
        "revision_count": 0,
        "final_answer": "",
    }
    completion_id = f"chatcmpl-{uuid.uuid4().hex}"
    created = int(time.time())
    model = request.model or get_settings().grok_model_name
    development = get_settings().app_env == "development"

    def trace(route: str, review: str, revisions: int, nodes: list[str]) -> None:
        if development:
            logger.info(
                "route=%s | review=%s | revisions=%d | nodes: %s",
                route,
                review,
                revisions,
                " → ".join(nodes),
            )

    if not request.stream:
        nodes: list[str] = []
        final: dict = dict(state)
        async for update in graph.astream(state, stream_mode="updates"):
            for node, values in update.items():
                nodes.append(node)
                final.update(values)
        trace(final["route"], final["review_decision"], final["revision_count"], nodes)
        return {
            "id": completion_id,
            "object": "chat.completion",
            "created": created,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"[route: {final['route']}]\n\n"
                        + final["final_answer"],
                    },
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
        nodes: list[str] = []
        final: dict = dict(state)
        try:
            async for update in graph.astream(state, stream_mode="updates"):
                for node, values in update.items():
                    nodes.append(node)
                    final.update(values)
                    if node == "router":
                        yield _sse(chunk({"content": f"[route: {final['route']}]\n\n"}))
            words = final["final_answer"].split(" ")
            for start in range(0, len(words), 4):
                text = " ".join(words[start : start + 4])
                if start + 4 < len(words):
                    text += " "
                yield _sse(chunk({"content": text}))
        except Exception as error:  # noqa: BLE001 - surface upstream failures in-stream
            yield _sse({"error": {"message": str(error)}})
        trace(final["route"], final["review_decision"], final["revision_count"], nodes)
        yield _sse(chunk({}, "stop"))
        yield _sse("[DONE]")

    return StreamingResponse(event_stream(), media_type="text/event-stream")
