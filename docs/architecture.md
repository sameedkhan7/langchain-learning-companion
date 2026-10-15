# Architecture — Learning Companion Chatbot

## Classroom flow

```
Open WebUI → this local application's OpenAI-compatible chat endpoint → LangChain prompt and Grok model → answer in Open WebUI
```

## Open WebUI

Open WebUI is already installed and working. It is the supplied chat client only. Participants must not reinstall, reconfigure, modify, or build it. The only thing recorded here is the connection value it points at (this app's `/v1` base URL).

## Capstone

One small **Learning Companion Chatbot**. There is no custom frontend and no second demonstration application.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Simple OK check |
| GET | `/v1/models` | OpenAI-style list with the one configured Grok model |
| POST | `/v1/chat/completions` | The single chat route (streaming and non-streaming) |

There is one chat route only.

## Boundaries

- API keys live only in an untracked `.env`.
- Application instructions (system prompt) stay separate from user messages.
- Out of scope for the course: authentication, authorization, security hardening, databases, persistent memory, RAG, production deployment, and extensive tests.

## Stack

Python 3.12, UV, FastAPI, Pydantic settings, `langchain` with the Grok-compatible provider integration (`langchain-xai`), Uvicorn, Ruff, and a minimal test runner (pytest).

## Configuration names

`APP_ENV`, `GROK_API_KEY`, `GROK_API_BASE_URL`, `GROK_MODEL_NAME`, `HOST`, `PORT`.

## Message flow

```
request → latest user message picked → prompt (system instruction, then user message) → Grok → text → JSON or SSE
```

A `system` message in the request is treated as user-provided content and is never used as the application's system instruction.

## No-persistence boundary

Nothing is stored between requests: no history, database, or memory. Each request is answered from the latest user message alone.

## Later growth

Story 2.1 is the prompt template. Story 2.2 adds conversation history on the same chain and the same chat endpoint. LangGraph and agents come later still.
