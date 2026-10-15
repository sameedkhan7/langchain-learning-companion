# Story 2.1 — LangChain Prompt Template

## Purpose

Make the seed's LangChain flow reusable and easy to read. The prompt gets two clearly separate parts: a stable Learning Companion instruction owned by the application, and the learner's current message. Participants can see exactly what is sent to Grok and in what order.

## What this story implements in plain English

After this story, a participant using the chatbot will notice:

- Chatting in Open WebUI works exactly as before: same model, same connection, same streamed and non-streamed replies.
- The Learning Companion always answers in the same friendly, patient style, because that instruction now lives in one clearly named place that the app owns.
- Whatever a chat window sends as a "system" message cannot change that style. It is treated as ordinary text from the user.
- Only the newest question is used. The chatbot still does not remember earlier messages (that comes in Story 2.2).
- While developing, the app can print a short summary such as "system, user — 2 messages". It never prints keys or the full hidden instruction.

## Prerequisites

- Story 1.1 is complete: the seed app, `.env`, and the existing Open WebUI connection work. Open WebUI must not be reinstalled, reconfigured, or modified.
- `docs/config.yaml` does not exist, so use the repository root (`langchain/`). If one appears, use the project path it configures.
- Read first: `docs/architecture.md`, `docs/stories/story-1-1-architecture-project-seed.md`, `.env.example`, `src/learning_companion/chain.py`, `src/learning_companion/api.py`, `src/learning_companion/settings.py`.
- No new dependencies. `langchain-core` (messages, prompts, parsers) is already installed through `langchain`. Do not run `uv add`.
- Preserve existing work: the three routes, the settings names, `.env.example`, the 503 configuration error, and everything under `handouts-session-*`.

## Work to do

1. **Rebuild the prompt in `src/learning_companion/chain.py`.**
   - Keep `SYSTEM_INSTRUCTION` as the one stable, application-owned instruction.
   - Build the prompt with LangChain's chat prompt abstractions: `ChatPromptTemplate.from_messages` with a `SystemMessage(content=SYSTEM_INSTRUCTION)` (a real message object, not a template string, so braces in the instruction are never treated as variables) followed by `("human", "{question}")`. Do not concatenate or format a large string by hand.
   - Expose the prompt as a small named module-level value or function (for example `build_prompt()`), so it can be inspected and reused in Story 2.2.
   - Keep the chain `prompt | ChatXAI model | StrOutputParser()`, with the same lazy model creation, the same Grok settings, and the same `ConfigurationError` messages.
2. **Add a compact development-only inspector** in `chain.py` (for example `describe_prompt(question) -> list[str]`) that formats the prompt with the question and returns only message roles and a count, such as `["system", "human"]`. It must not return or log message content, API keys, or the full instruction.
3. **Log it only in development.** In `api.py`, when `APP_ENV == "development"`, log one line per chat request using the standard `logging` module: the roles in order, the count, and whether a request-supplied `system` message was set aside. No message text, no keys.
4. **Keep using the latest supported user message only** in `api.py`.
   - A `system` message in the request is treated as user-provided content and never becomes, or replaces, the application's system instruction. In this story it is not forwarded as a system message, and no history is used.
   - Pass the single latest `user` message to the chain as `{"question": ...}`.
5. **One chain, both paths.** `chain.ainvoke` (normal JSON) and `chain.astream` (SSE) must keep using this same chain from `get_chain()`. Do not add a second chain, route, or custom message format. Response shapes, status codes, `[DONE]` handling, and `/v1/models` stay unchanged.
6. **Update `docs/architecture.md`.**
   - Add a short **Message flow** section: request → latest user message picked → prompt (system instruction, then user message) → Grok → text → JSON or SSE.
   - Add the deliberate **no-persistence boundary**: nothing is stored between requests; no history, database, or memory.
   - Fix "Later growth": Story 2.1 is the prompt template; Story 2.2 adds conversation history.
7. **Fill in the Handover** below when done.

### Files created or changed

`src/learning_companion/chain.py`, `src/learning_companion/api.py`, `docs/architecture.md`, `docs/stories/story-2-1-langchain-prompt-template.md` (Handover only). No new dependencies, so `pyproject.toml` and `uv.lock` stay unchanged.

### Not in this story

A command-line-only chatbot, a second chat path, conversation history, a database, persistent memory, RAG, tools, MCP, LangGraph, a new frontend, an evaluation harness, a broad test suite, or any security programme.

## Completion checks

Keep it small. Record the commands you actually run.

1. Format and lint: `uv run ruff format .` then `uv run ruff check .`
2. Start the API with the port Open WebUI already points at (Story 1.1 used `--port 8011` because 8000 was busy): `uv run uvicorn learning_companion.api:app --host 127.0.0.1 --port 8011`, with `APP_ENV=development`.
3. In the **existing** Open WebUI, select the configured model and ask one ordinary question, such as "Explain what a variable is."
4. In the app's terminal, confirm the development log shows the roles in order, `system` then `human`, with a count of 2, and no keys or instruction text.
5. Confirm Open WebUI still renders a streamed answer in the Learning Companion's friendly style.

**Expected Open WebUI result:** the same chat experience as Story 1.1. One ordinary question gets a short, plain-language Grok answer, and the connection settings are unchanged.

## Handover

When finished, record here:

- **Commands run:**
  - `uv run ruff format .` — failed on junk `__MACOSX/` files (invalid UTF-8, pre-existing); it still reformatted one file.
  - `uv run ruff format src` — passed.
  - `uv run ruff check src` — passed.
  - `uv run python -c "from learning_companion.chain import describe_prompt; print(describe_prompt('hi {x}'))"` — passed, printed `['system', 'human']`.
- **Files created or changed:** `src/learning_companion/chain.py`, `src/learning_companion/api.py`, `docs/architecture.md`, this story file (Handover only).
- **Verified:** format/lint on `src`; prompt order is system then human (count 2) via `describe_prompt`, and braces in the question are safe.
- **Not verified:** running the API, the development log line in the live terminal, a question in Open WebUI, the streaming and non-streaming paths against Grok, and a request-supplied `system` message. These need the real Grok key and Open WebUI.
- **Open WebUI connection value:** unchanged from Story 1.1.

**What Story 2.2 will extend:** the same prompt and chain. Story 2.2 adds conversation history: earlier user and assistant messages from the request will be placed between the system instruction and the current question, and it will decide how request-supplied `system` messages are handled. It adds no new routes or app.
