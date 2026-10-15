# Story 3.1 — Study-Helper Chain

## Purpose

Give the Learning Companion a second, separately named LangChain behaviour: a study helper that explains beginner technical concepts and ends with one small next step. This story builds the capability only. The chat endpoint keeps using the existing general-chat chain; choosing between the two is Story 3.2.

## What this story implements in plain English

After this story, a participant working on the project can:

- Ask the study helper (from a small local command, not yet from Open WebUI) to explain a beginner concept such as "What is an API?" in plain language.
- Get a short explanation, a small example where it helps, and exactly one suggested next learning step.
- Use the same Grok model and the same recent conversation history as the existing chatbot. No new model, app, or endpoint is involved.
- Keep chatting in Open WebUI exactly as before. Greetings and ordinary questions still go to the unchanged general-chat chain.
- Know the study helper is a prompt for Grok, not a researcher. It does not browse, look up course material, or promise its answers are correct.

## Prerequisites

- Stories 1.1, 2.1, and 2.2 are complete: the three routes, Grok settings, the general-chat prompt and chain, request-provided history, and the existing Open WebUI connection all work. Open WebUI must not be reinstalled, reconfigured, or modified.
- `docs/config.yaml` does not exist, so use the repository root (`langchain/`). If one appears, use the project path it configures.
- Read first: `docs/architecture.md`, Stories 1.1–2.2, `.env.example`, `src/learning_companion/chain.py`, `src/learning_companion/api.py` (the OpenAI-compatible chat adapter), `src/learning_companion/settings.py`.
- No new dependencies. Do not run `uv add`.
- Preserve existing work: the three routes, request and response shapes, SSE `[DONE]` handling, the 503 configuration error, the settings names and `.env.example` (both unchanged), history handling (`_build_history`, `MAX_HISTORY_MESSAGES`), and everything under `handouts-session-*`.

## Work to do

1. **Leave the general-chat chain untouched** in `src/learning_companion/chain.py`: `SYSTEM_INSTRUCTION`, `build_prompt`, `describe_prompt`, and `get_chain` are not edited. `api.py` is not edited either, so `/v1/chat/completions` still uses `get_chain()`.
2. **Add the study-helper chain** in `src/learning_companion/chain.py`, below the existing code:
   - `STUDY_SYSTEM_INSTRUCTION`: a separate, app-owned instruction. It asks for a concise plain-language explanation of a beginner technical concept, a small example where useful, and exactly one suggested next learning step at the end. It states that the helper does not research, browse, retrieve course data, or guarantee correctness, and must not claim to. It is never built from user content.
   - `build_study_prompt()`: a `ChatPromptTemplate` shaped like the existing one: `SystemMessage(STUDY_SYSTEM_INSTRUCTION)`, `MessagesPlaceholder("history", optional=True)`, `("human", "{question}")`. It takes the same `question` and `history` inputs, so the same request history can be passed in.
   - `get_study_chain()`: cached with `lru_cache`, returning `build_study_prompt() | ChatXAI model | StrOutputParser()`. It reads the same settings (`GROK_API_KEY`, `GROK_API_BASE_URL`, `GROK_MODEL_NAME`) and raises the same `ConfigurationError` messages. A little repeated model-setup code is fine here; do not refactor `get_chain` to share it.
3. **Add a small project-local development entry point**, `src/learning_companion/study_dev.py`, run as `uv run python -m learning_companion.study_dev "What is an API?"`:
   - Takes the question as a command-line argument, calls `get_study_chain().invoke({"question": question, "history": []})`, and prints the text.
   - On `ConfigurationError`, prints the message and exits non-zero.
   - Prints no keys or instruction text. It is not wired to any route, endpoint, or UI.
4. **Update `docs/architecture.md`** with a short **Chain behaviours** section:
   - **General chat** (`get_chain`): greetings and ordinary conversation; the active chain behind `/v1/chat/completions`.
   - **Study helper** (`get_study_chain`): beginner technical explanations with one next step; available after this story but **not yet reachable from Open WebUI**.
   - Both use the same Grok model, the same request-provided history, the same endpoint, and the same Open WebUI conversation. This story creates the study-helper capability only; selecting between chains is Story 3.2.
   - Update **Later growth** to say Story 3.1 adds the study-helper chain and Story 3.2 adds the route rule.
5. **Fill in the Handover** below when done.

### Files created or changed

`src/learning_companion/chain.py` (additions only), `src/learning_companion/study_dev.py` (new), `docs/architecture.md`, `docs/stories/story-3-1-study-helper-chain.md` (Handover only). `api.py`, `settings.py`, `pyproject.toml`, `uv.lock`, and `.env.example` stay unchanged.

### Not in this story

Routing or any `/study` rule (Story 3.2), LLM-based classification, more specialists, loops, review steps, a second app, endpoint, model provider, UI, database, retrieval, MCP server, tool calls, LangGraph, an autonomous agent, broad tests, or production controls.

## Completion checks

Keep it small. Record the commands you actually run.

1. Format and lint: `uv run ruff format src` then `uv run ruff check src` (not `.`, which trips over the junk `__MACOSX/` files).
2. General chat unchanged: start the API (`uv run uvicorn learning_companion.api:app --host 127.0.0.1 --port 8011`), and in the **existing** Open WebUI send one ordinary message such as "Hello!". Confirm it answers as before in the general-chat style, with no forced next-step ending.
3. Study helper, one focused local call: `uv run python -m learning_companion.study_dev "What is an API?"`.
4. Confirm the study-helper answer contains a plain explanation and exactly one suggested next step.

**Expected results:** the Open WebUI reply is the same friendly general-chat behaviour as in Story 2.2. The local study-helper output is a short plain-language explanation of an API, a small example, and one next step at the end, with no claim of browsing, research, or guaranteed accuracy.

## Handover

When finished, record here:

- **Commands run:** `uv run ruff format src` (1 file reformatted), `uv run ruff check src` (all checks passed), `uv run python -m learning_companion.study_dev "What is an API?"`.
- **Files created or changed:** `src/learning_companion/chain.py` (additions only), `src/learning_companion/study_dev.py` (new), `docs/architecture.md`, this story (Handover).
- **Verified:** format and lint pass; `git diff` shows `chain.py` is additions only and `api.py` is untouched; the dev entry point runs and, with no key set, prints `GROK_API_KEY is not set. Add it to your .env file.` and exits 1.
- **Not verified:** the live study-helper answer (explanation plus one next step) and the Open WebUI general-chat message, because there is no `.env` with `GROK_API_KEY` in this workspace. Run checks 2-4 once the key is in place.
- **Open WebUI connection value:** unchanged from Story 1.1 (nothing touched).

**What Story 3.2 will extend:** the same two chains and the single chat endpoint. Story 3.2 adds the visible `/study` route rule in Python so a message starting with `/study` goes to `get_study_chain()` and everything else still goes to `get_chain()`, using the same history and Open WebUI conversation. It is plain routing, not an agent.
