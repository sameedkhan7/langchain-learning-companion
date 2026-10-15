# Story 1.1 — Architecture and Project Seed

## Purpose

Agree the shape of the Learning Companion Chatbot, then create the smallest working project behind it. Participants finish with one Grok reply showing in the Open WebUI they already use.

This story runs in two stages with a hard stop between them: **Stage A (architecture, needs instructor approval)** and **Stage B (project seed, only after approval)**.

## What this story implements in plain English

After this story, a participant can:

- Start a small chat service on their own computer with one command.
- Check that the service is alive and that it lists one model to choose from.
- Pick that model in their existing Open WebUI and send a message.
- See a reply from Grok appear in Open WebUI, both all at once and typed out word by word.
- Keep their secret key in a private file that is never shared or committed.

## Prerequisites

- Python 3.12 and UV are installed.
- Open WebUI is already installed and working for participants. It is only the supplied chat window. **Do not reinstall, reconfigure, modify, or build it.**
- The instructor has supplied the Grok model name. The participant has a Grok API key.
- Project path: no `docs/config.yaml` exists, so use the repository root (`langchain/`). If one appears later, use the project path it configures.
- No `docs/architecture.md` and no other stories exist yet. Preserve everything already in the repository (`handouts-session-*`, `langchain.md`, and so on).

## Work to do

### Stage A — Architecture (do this first, then stop)

1. Create `docs/architecture.md` (or update it if it exists, keeping existing content). Keep it short and plain. It must record:
   - **The single classroom flow:**
     `Open WebUI → this local application’s OpenAI-compatible chat endpoint → LangChain prompt and Grok model → answer in Open WebUI`
   - **Open WebUI** is already installed and working. It is the supplied chat client only. Participants must not reinstall, reconfigure, modify, or build it.
   - **The capstone** is one small **Learning Companion Chatbot**. There is no custom frontend and no second demonstration application.
   - **Endpoints:** `GET /health`, `GET /v1/models`, `POST /v1/chat/completions`. There is one chat route only.
   - **Boundaries (light):**
     - API keys live only in an untracked `.env`.
     - Application instructions stay separate from user messages.
     - Out of scope for the course: authentication, authorization, security hardening, databases, persistent memory, RAG, production deployment, and extensive tests.
   - **Stack:** Python 3.12, UV, FastAPI, Pydantic settings, `langchain` with the Grok-compatible provider integration, Uvicorn, Ruff, and a minimal test runner.
   - **Configuration names:** `APP_ENV`, `GROK_API_KEY`, `GROK_API_BASE_URL`, `GROK_MODEL_NAME`, `HOST`, `PORT`.
   - **Later growth:** Story 2.1 adds full prompt construction and conversation history. LangGraph and agents come later still.
2. **Ask the instructor to approve `docs/architecture.md`.** Show them the path and a two-line summary.
3. **STOP.** Until the instructor explicitly approves, do **not** create seed files, install dependencies, or scaffold code. Resume this same story only after explicit approval. If they request changes, edit the architecture and ask again.

### Stage B — Project seed (only after explicit approval)

1. Initialise a Python 3.12 UV project at the project path. Add runtime dependencies: `fastapi`, `uvicorn`, `pydantic-settings`, `langchain`, and the Grok-compatible LangChain provider integration (`langchain-xai`). Add dev dependencies: `ruff` and `pytest`. Commit the resulting `uv.lock`.
2. Create `.env.example` with exactly these settings and nothing else (no Claude, other-provider, database, or production values):

   ```
   APP_ENV=development
   GROK_API_KEY=
   GROK_API_BASE_URL=https://api.x.ai/v1
   GROK_MODEL_NAME=
   HOST=127.0.0.1
   PORT=8000
   ```

3. Create `.gitignore` that ignores at least `.env`, `.venv/`, `__pycache__/`, `.ruff_cache/`, and `.pytest_cache/`. `.env.example` stays tracked.
4. Create the package `src/learning_companion/` with small modules, for example:
   - `__init__.py`
   - `settings.py` — Pydantic settings reading the six names above from `.env`. All values must have defaults or be allowed blank so the app **starts without a real API key**.
   - `chain.py` — one LangChain flow: chat prompt → Grok chat model → text output parser. The prompt has a fixed Learning Companion system instruction (kept separate from the user message) and the **latest user message** only. Build the model lazily, on the first call. If `GROK_API_KEY` or `GROK_MODEL_NAME` is blank, raise a clear error at that point.
   - `api.py` (or `main.py`) — the FastAPI app with the three routes below.
5. Routes (and no others):
   - `GET /health` returns a simple OK JSON object.
   - `GET /v1/models` returns the OpenAI-style model list containing the configured `GROK_MODEL_NAME` as the one selectable model. If the name is blank, return an empty list.
   - `POST /v1/chat/completions` accepts `model`, `messages` (a list of text messages with role `system`, `user`, or `assistant`), and `stream`.
     - `stream: false` → normal OpenAI-compatible chat-completion JSON with the reply text.
     - `stream: true` → text-only OpenAI-compatible SSE: `data:` chunks carrying text deltas, then a final chunk with `finish_reason: "stop"`, then `data: [DONE]`.
     - Both modes use the **same** chain from step 4. Only the latest `user` message goes to the model in this story; history is ignored for now.
     - A missing key or model name gives an honest error (HTTP 503 with a plain message such as "GROK_API_KEY is not set. Add it to your .env file."). It must happen only when a model call is attempted, never at startup, `/health`, or `/v1/models`.
   - Do not add custom Open WebUI events, a second chat route, tool calls, or a browser UI.
6. Create `tests/` with one tiny test only (for example, `/health` returns OK). No broad test suite.
7. Create `README.md` covering: what the project is, `uv sync`, copying `.env.example` to `.env`, that the **instructor supplies `GROK_MODEL_NAME`** and the participant puts their real key **only in the untracked `.env`**, the start command, and the Open WebUI connection note below.
8. **Open WebUI connection note** (document in the README, application side only): the existing Open WebUI connection should point at this app’s base URL `http://127.0.0.1:8000/v1` (use `http://host.docker.internal:8000/v1` if Open WebUI runs in Docker), with any placeholder API key if it insists on one, and the configured model selected in the model picker. Only record the value to enter. Do not change Open WebUI’s code, install, or settings beyond that existing connection entry. If Docker cannot reach `127.0.0.1`, tell the instructor rather than changing the default `HOST` in `.env.example`.

### Files created or changed

Stage A: `docs/architecture.md`.
Stage B: `pyproject.toml`, `uv.lock`, `.env.example`, `.gitignore`, `README.md`, `src/learning_companion/__init__.py`, `src/learning_companion/settings.py`, `src/learning_companion/chain.py`, `src/learning_companion/api.py`, `tests/test_health.py`.
Also created locally by the participant and never committed: `.env`.

### Not in this story

LangGraph, agents, MCP, tool calls, conversation history, advanced streaming, authentication, databases, RAG, and a broad test suite.

## Completion checks

Run only these lightweight checks, and record the commands actually run in the Handover.

1. Format and lint: `uv run ruff format .` then `uv run ruff check .`
2. Start the API: `uv run uvicorn learning_companion.api:app --host 127.0.0.1 --port 8000` (adjust the module path to match the real file). It must start with a blank `GROK_API_KEY`.
3. Health: `curl http://127.0.0.1:8000/health` returns OK.
4. Model discovery: `curl http://127.0.0.1:8000/v1/models` lists the configured Grok model (with `.env` filled in).
5. In the **existing** Open WebUI, select that model and send one message with normal (streamed) chat. A Grok reply appears.
6. Send one **non-streaming** request. Use the per-chat option in Open WebUI chat controls to turn streaming off if it is offered. Otherwise send `POST /v1/chat/completions` with `"stream": false` using curl and confirm normal JSON comes back.
7. Blank-key check: with `GROK_API_KEY` empty, a chat request returns the honest configuration error and the app stays up.
8. Confirm `.env` is untracked and holds the only copy of the real key.

**Expected classroom result:** one Grok reply visible in Open WebUI.

## Handover

When finished, record here:

- **Architecture approval:** `docs/architecture.md` approved by the instructor/user (sameedk499@gmail.com) on 2026-10-15, in chat ("approve"), before any Stage B work.
- **Commands run:**
  - `uv init --bare --name learning-companion --python 3.12 .` — passed.
  - `uv add fastapi uvicorn pydantic-settings langchain langchain-xai` and `uv add --dev ruff pytest httpx` — passed.
  - `uv sync` — passed.
  - `uv run ruff format .` — passed (also prints "Failed to read" errors for junk `__MACOSX` files; harmless).
  - `uv run ruff check .` — passed (after adding `# noqa: BLE001` on the in-stream error catch).
  - `uv run pytest -q` — 1 passed.
  - `uv run uvicorn learning_companion.api:app --host 127.0.0.1 --port 8011` with blank `GROK_API_KEY` — started OK. Port 8011 was used because port 8000 is occupied by an unrelated RAG app on this machine.
  - `curl /health` — returned `{"status":"ok"}`, passed.
  - `curl /v1/models` with blank model name — returned an empty list, passed.
  - `POST /v1/chat/completions` (`stream: true`) with blank key — HTTP 503 "GROK_API_KEY is not set. Add it to your .env file."; `/health` still OK afterwards, passed.
- **Files created or changed:** `docs/architecture.md`, `pyproject.toml`, `uv.lock`, `.env.example`, `.gitignore`, `README.md`, `src/learning_companion/__init__.py`, `settings.py`, `chain.py`, `api.py`, `tests/test_health.py`. Not committed: `.env` (does not exist yet). Beyond the list: `httpx` dev dependency (needed by FastAPI's test client) and a hatchling `[build-system]` section so the package imports under uvicorn.
- **Open WebUI connection value:** base URL `http://127.0.0.1:8000/v1` (or `http://host.docker.internal:8000/v1` for Docker); model name = the instructor-supplied `GROK_MODEL_NAME`. Not actually entered into Open WebUI yet. If port 8000 stays busy, use `--port 8001` and `http://127.0.0.1:8001/v1`.
- **Not verified:**
  - No real Grok reply, streamed or non-streamed (no API key or model name available).
  - `/v1/models` with a model name filled in.
  - Selecting the model and chatting in the existing Open WebUI.
  - The `stream: false` request path, including the 503 case (only the streaming 503 was exercised).
  - Docker reachability of `127.0.0.1`.
  - That `.env` holds the only copy of the real key (no `.env` exists yet; it is in `.gitignore`; the directory is not a git repository, so tracking was not checked with git).

**What Story 2.1 will extend:** the same chain and the same single chat endpoint. Story 2.1 replaces the fixed one-message prompt with a full prompt built from system, user, and conversation messages, and adds conversation history. It does not add new routes or a new app.
