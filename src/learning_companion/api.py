import json
import time
import uuid
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from learning_companion.chain import ConfigurationError, get_chain
from learning_companion.settings import get_settings

app = FastAPI(title="Learning Companion Chatbot")


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


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


def _latest_user_message(messages: list[Message]) -> str:
    for message in reversed(messages):
        if message.role == "user":
            return message.content
    return ""


def _sse(payload: dict | str) -> str:
    body = payload if isinstance(payload, str) else json.dumps(payload)
    return f"data: {body}\n\n"


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    try:
        chain = get_chain()
    except ConfigurationError as error:
        return JSONResponse(status_code=503, content={"error": {"message": str(error)}})

    question = _latest_user_message(request.messages)
    completion_id = f"chatcmpl-{uuid.uuid4().hex}"
    created = int(time.time())
    model = request.model or get_settings().grok_model_name

    if not request.stream:
        text = await chain.ainvoke({"question": question})
        return {
            "id": completion_id,
            "object": "chat.completion",
            "created": created,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": text},
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
        try:
            async for piece in chain.astream({"question": question}):
                if piece:
                    yield _sse(chunk({"content": piece}))
        except Exception as error:  # surface upstream failures inside the stream
            yield _sse({"error": {"message": str(error)}})
        yield _sse(chunk({}, "stop"))
        yield _sse("[DONE]")

    return StreamingResponse(event_stream(), media_type="text/event-stream")
