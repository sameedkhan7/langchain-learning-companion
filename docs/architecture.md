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
request → latest user message picked and history built (last 6 earlier user/assistant messages, in order) → route rule (`/study` prefix or not) → selected chain (`get_study_chain` or `get_chain`: system instruction, history, question) → Grok → text with route label → JSON or SSE
```

### The `/study` rule

If the trimmed latest user message is `/study` alone, or starts with `/study` followed by whitespace, the route is `study` and only that leading marker (and surrounding whitespace) is stripped. The marker is case-sensitive. A bare `/study` uses the fixed fallback question "What should I study first as a beginner?". Anything else, including `/studying` or `/study` mid-sentence, is `general` with the question unchanged. Earlier history messages are never rewritten.

The reply text starts with `[route: general]` or `[route: study]` and a blank line; in development the log line also states the route. The label then appears in later requests' history as part of the earlier assistant message.

This is **deterministic application routing** (one plain Python `if`/`else`), not LLM classification, LangGraph, or multi-agent orchestration.

A `system` message in the request is treated as user-provided content and is never used as the application's system instruction.

## No-persistence boundary

Conversation history comes only from the current Open WebUI request. The application saves nothing after a request completes and adds no database or cross-session memory.

## Chain behaviours

| Behaviour | Function | Responsibility |
|-----------|----------|----------------|
| General chat | `get_chain` | Greetings and ordinary conversation. The active chain behind `/v1/chat/completions`. |
| Study helper | `get_study_chain` | Beginner technical explanations ending with one next learning step. Reachable from Open WebUI by starting a message with `/study`. |

Both use the same Grok model, the same request-provided history, the same endpoint, and the same Open WebUI conversation. Story 3.1 created the study-helper chain; Story 3.2 selects between the chains with the `/study` rule.

## Later growth

Story 2.1 is the prompt template. Story 2.2 adds request-provided history on the same chain and chat endpoint. Story 3.1 adds the study-helper chain, and Story 3.2 adds the route rule that selects between the chains, and Story 4.1 replaces the internal `if/else` with an explicit LangGraph route. Agents come later still.
