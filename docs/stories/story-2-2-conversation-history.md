# Story 2.2 — Conversation History

## Purpose

Let the Learning Companion answer a follow-up question using the earlier messages of the same chat. Open WebUI already sends those messages with every request; this story passes a short recent slice of them into the existing prompt, and nothing more.

## What this story implements in plain English

After this story, a participant using the chatbot will notice:

- If they ask "What is a variable?" and then "Can you give me an example of that?", the second answer is about variables, because the chatbot can see the earlier question and answer.
- The chatbot only looks at the most recent few messages of the current chat (at most 6 earlier messages, which is 3 question-and-answer turns). Older messages are simply left out.
- The chatbot forgets everything once a request is finished. It stores nothing. A new chat, or a restart of the app, starts fresh.
- Its friendly, patient style does not change. A "system" message sent by the chat window is still treated as ordinary text and can never replace the app's own instruction.
- While developing, the app prints one short line such as "system, human, ai, human — 4 messages". It never prints keys, the hidden instruction, or message text.

## Prerequisites

- Stories 1.1 and 2.1 are complete: the three routes, Grok settings, the LangChain prompt template, and the existing Open WebUI connection all work. Open WebUI must not be reinstalled, reconfigured, or modified.
- `docs/config.yaml` does not exist, so use the repository root (`langchain/`). If one appears, use the project path it configures.
- Read first: `docs/architecture.md`, Stories 1.1 and 2.1, `.env.example`, `src/learning_companion/chain.py`, `src/learning_companion/api.py` (the OpenAI-compatible chat adapter), `src/learning_companion/settings.py`.
- No new dependencies. `langchain-core` already provides `MessagesPlaceholder`, `HumanMessage`, and `AIMessage`. Do not run `uv add`.
- Preserve existing work: the three routes, request and response shapes, the settings names, `.env.example` (unchanged; the message limit is a code constant, not a new setting), the 503 configuration error, SSE `[DONE]` handling, and everything under `handouts-session-*`.

## Work to do

1. **Add a history slot to the prompt in `src/learning_companion/chain.py`.**
   - Keep `SYSTEM_INSTRUCTION` and the `SystemMessage` as the first prompt item.
   - Add `MessagesPlaceholder("history", optional=True)` between the system message and `("human", "{question}")`. Do not build an ad-hoc prompt string.
   - Add one documented constant, `MAX_HISTORY_MESSAGES = 6`, with a one-line comment explaining that it counts earlier user and assistant messages, excluding the latest question.
   - Keep the chain `prompt | ChatXAI model | StrOutputParser()` with the same lazy model creation, Grok settings, and `ConfigurationError` messages.
2. **Convert request messages to history in `src/learning_companion/api.py`.**
   - Choose the latest supported `user` message as the question (as today). The history is the supported `user` and `assistant` messages that come **before** it, in their original order, converted to `HumanMessage` and `AIMessage`.
   - Keep only the last `MAX_HISTORY_MESSAGES` of them.
   - Make a small helper (for example `_build_history(messages) -> tuple[str, list[BaseMessage]]`) so the logic is easy to read.
   - **Safe ignoring:** a `system` message is never forwarded and never replaces the application's instruction. Messages with empty or non-text content are skipped. Open WebUI may send content as a list of parts; keep only the `text` parts joined together and ignore the rest (images, files). Roles other than `system`, `user`, and `assistant` (for example `tool`) are skipped rather than causing an error. Loosen the `Message` model just enough to accept this without a 422; response shapes stay unchanged.
3. **One chain, both paths.** `chain.ainvoke` (JSON) and `chain.astream` (SSE) both receive `{"question": ..., "history": [...]}` from the same `get_chain()`. No second chain, route, or message format. Status codes, `[DONE]` handling, and `/v1/models` stay unchanged.
4. **Update the compact development inspector.** Extend `describe_prompt` in `chain.py` (or replace it with an equivalent helper) to take the question and history and return only the message roles in order and a count, for example `["system", "human", "ai", "human"]`, 4 messages. It never returns or logs message content, API keys, or the instruction text.
5. **Log it only in development.** In `api.py`, when `APP_ENV == "development"`, log one line per chat request using the standard `logging` module: roles in order, message count, and whether a request-supplied `system` message was set aside. No message text, no keys.
6. **Update `docs/architecture.md`.**
   - Extend **Message flow**: request → latest user message picked, earlier supported `user`/`assistant` messages converted in order and trimmed to the last 6 → prompt (system instruction, history, latest user message) → Grok → text → JSON or SSE.
   - Update the **No-persistence boundary**: history comes only from the current Open WebUI request; the application saves nothing after a request completes and adds no database or cross-session memory.
   - Update **Later growth**: Story 2.2 adds request-provided history; Story 3.1 builds on it.
7. **Fill in the Handover** below when done.

### Files created or changed

`src/learning_companion/chain.py`, `src/learning_companion/api.py`, `docs/architecture.md`, `docs/stories/story-2-2-conversation-history.md` (Handover only). No new dependencies, so `pyproject.toml`, `uv.lock`, and `.env.example` stay unchanged.

### Not in this story

A database, persistent or cross-session memory, summarising old messages, RAG, tools, MCP, routing, LangGraph, a new endpoint, a new UI, an evaluation harness, a broad test suite, or production memory features.

## Completion checks

Keep it small. Record the commands you actually run.

1. Format and lint: `uv run ruff format src` then `uv run ruff check src` (running `ruff` on `.` trips over the junk `__MACOSX/` files, as noted in Story 2.1).
2. Start the API on the port Open WebUI already points at, with `APP_ENV=development`: `uv run uvicorn learning_companion.api:app --host 127.0.0.1 --port 8011`.
3. In the **existing** Open WebUI, start a **new chat**, select the configured model, and ask: "What is a variable?"
4. In the same chat, ask: "Can you give me an example of that?"
5. In the app's terminal, confirm the development log for the first request shows roles `system, human` (2 messages) and for the second request shows `system, human, ai, human` (4 messages), with no keys, instruction text, or message bodies.
6. Confirm both answers stream normally in Open WebUI.

**Expected Open WebUI result:** the first answer explains what a variable is in a short, friendly way. The second answer gives an example of a variable, without the learner repeating the topic, showing that the earlier question and answer were used. Starting a new chat and asking only "Can you give me an example of that?" gets no such context.

## Handover

When finished, record here:

- **Commands run:** `uv run ruff format src` (passed, reformatted 1 file); `uv run ruff check src` (passed); an inline `uv run python -c` check of `_build_history` and `describe_prompt` (passed).
- **Files created or changed:** `src/learning_companion/chain.py`, `src/learning_companion/api.py`, `docs/architecture.md`, this Handover.
- **Verified:** format/lint; with a sample request (system, user, assistant, tool, list-style user content) the helper dropped `system` and `tool`, kept only text parts, picked the latest user message, and `describe_prompt` gave `system, human, ai, human`; a 20-message chat was trimmed to 6 history messages.
- **Not verified:** the live Open WebUI run (new chat, "What is a variable?" then the follow-up) and the development log lines against the running app; real Grok calls; the non-streaming path.
- **Open WebUI connection value:** unchanged from Story 1.1.

**What Story 3.1 will extend:** the same prompt, chain, and single chat endpoint. Story 3.1 builds the study-helper chain on top of this request-provided history, changing what the application asks Grok to do with the conversation. It still adds no database, no cross-session memory, and no new endpoint or app.
