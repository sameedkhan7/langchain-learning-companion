# Story 3.2 — Visible Python Routing

## Purpose

Make both existing chains reachable from the same Open WebUI chat, using one deliberately plain Python `if/else` that participants can read in a few seconds. Story 3.1 built the study-helper chain but nothing could reach it from Open WebUI. This story adds the rule that does. Session 4 will later replace this `if/else` with an explicit LangGraph route.

## What this story implements in plain English

After this story, a participant using the existing Open WebUI chat will notice:

- An ordinary message such as "Hello!" takes the **general** path: the app picks the general-chat chain, exactly as before.
- A message that starts with `/study`, such as `/study Explain what an API is`, takes the **study** path: the app picks the study-helper chain and passes it the question without the `/study` marker.
- Both messages go to the same endpoint, in the same Open WebUI conversation, with the same Grok model and the same recent-history rules as Story 2.2. Only the chain that answers is different.
- The reply starts with a short label, `[route: general]` or `[route: study]`, and the development log prints the same route word, so the choice is visible.
- The rule is plain application code, not an AI decision. Nothing is classified by a model, and nothing is decided on its own.

## Prerequisites

- Stories 1.1, 2.1, 2.2, and 3.1 are complete: the three routes, Grok settings, the general-chat chain (`get_chain`), the study-helper chain (`get_study_chain`), request-provided history, and the existing Open WebUI connection all work. Open WebUI must not be reinstalled, reconfigured, or modified.
- `docs/config.yaml` does not exist, so use the repository root (`langchain/`). If one appears, use the project path it configures.
- Read first: `docs/architecture.md`, Stories 1.1–3.1, `.env.example`, `src/learning_companion/chain.py`, `src/learning_companion/api.py` (the OpenAI-compatible chat adapter), `src/learning_companion/settings.py`.
- No new dependencies. Do not run `uv add`.
- Preserve existing work: the three routes, request and response shapes, SSE `[DONE]` handling, the 503 configuration error, the settings names and `.env.example` (unchanged), `_build_history` and `MAX_HISTORY_MESSAGES`, both chains' prompts, and everything under `handouts-session-*`.

## Work to do

1. **Add the route rule in `src/learning_companion/api.py`**, as a small, readable helper, for example `_choose_route(question: str) -> tuple[str, str]` returning `(route, question_for_chain)`:
   - If the question is `/study` alone, or starts with `/study` followed by whitespace, the route is `"study"`. The marker is case-sensitive, and the match is checked on the already-trimmed latest user message. Strip only that leading `/study` marker and surrounding whitespace. Do not touch the rest of the text. `/studying` and a `/study` in the middle of a sentence are ordinary general messages.
   - Anything else is `"general"` with the question unchanged.
   - Keep it a plain `if`/`else` with no regex framework, scoring, model call, or config setting. A bare `/study` with nothing after it uses one fixed fallback question, `"What should I study first as a beginner?"`, so the study chain is never called with an empty question.
2. **Keep the history rules from Story 2.2.** `_build_history` is not changed: it still picks the latest user message as the question and keeps up to 6 earlier user/assistant messages in order. Only the current question has `/study` stripped. Earlier messages, including earlier `/study ...` user messages and earlier labelled assistant replies, stay as they are, and a `system` message in the request is still set aside.
3. **Select the chain with the route.** In `chat_completions`, choose `get_study_chain()` for `study` and `get_chain()` for `general`. The 503 `ConfigurationError` handling covers both. Both chains receive `{"question": ..., "history": [...]}`, so the existing `ainvoke` (JSON) and `astream` (SSE) code paths serve both routes. No second endpoint, route, or message format.
4. **Record the route in development.** Extend the existing `APP_ENV == "development"` log line (or add one beside it) so it also says `route: general` or `route: study`. For the prompt-role summary of a study request, use the study prompt, so the line reflects what is really sent. Do this with a small optional argument or helper in `chain.py` (`describe_prompt` stays content-free). No message text, no keys, no instruction text.
5. **Add the route label to the answer text.** Prefix the reply with `[route: general]` or `[route: study]` followed by a blank line:
   - Non-streaming: the `content` is the label plus the chain's text.
   - Streaming: send the label as the first normal `content` delta, then stream the chain's pieces as today.
   - Do not add custom response fields, events, or Open WebUI plugins. The JSON and SSE shapes, the final `stop` chunk, and `[DONE]` are unchanged. Note that the label then appears in later requests' history as part of the earlier assistant message. That is accepted for this classroom story.
6. **Update `docs/architecture.md`:**
   - Extend **Message flow** with the route step: request → latest user message picked and history built → route rule (`/study` prefix or not) → selected chain (`get_study_chain` or `get_chain`) → Grok → text with route label → JSON or SSE.
   - State the **`/study` rule** exactly as in step 1.
   - Update **Chain behaviours**: the study helper is now reachable from Open WebUI by starting a message with `/study`.
   - Add the boundary: this is **deterministic application routing**, not LLM classification, LangGraph, or multi-agent orchestration.
   - Update **Later growth**: Story 3.2 adds the route rule, and Story 4.1 replaces the internal `if/else` with an explicit LangGraph route.
7. **Fill in the Handover** below when done.

### Files created or changed

`src/learning_companion/api.py`, `src/learning_companion/chain.py` (only the small development-summary tweak in step 4, if needed), `docs/architecture.md`, `docs/stories/story-3-2-visible-python-routing.md` (Handover only). `settings.py`, `study_dev.py`, `pyproject.toml`, `uv.lock`, and `.env.example` stay unchanged.

### Not in this story

LLM-based routing or classification, more specialists, review or improve steps, loops, retries, LangGraph, an autonomous agent, tool calls, MCP, a second app, endpoint, or UI, custom response fields, Open WebUI plugins, a broad test suite, or production controls.

## Completion checks

Keep it small. Record the commands you actually run.

1. Format and lint: `uv run ruff format src` then `uv run ruff check src` (not `.`, which trips over the junk `__MACOSX/` files).
2. Start the API with `APP_ENV=development` on the port Open WebUI already points at: `uv run uvicorn learning_companion.api:app --host 127.0.0.1 --port 8011`.
3. In the **existing** Open WebUI, in one conversation, send: `Hello!`
4. In the same conversation, send: `/study Explain what an API is`
5. Inspect the app's terminal log for the two requests.

**Expected Open WebUI results:**

- **General message:** a short, friendly reply that starts with `[route: general]`. There is no forced next-step ending.
- **`/study Explain what an API is`:** a reply that starts with `[route: study]`, then a clear plain-language explanation of an API (with a small example where useful), ending with exactly one suggested next learning step. It makes no claim of browsing, research, or guaranteed accuracy.
- Both replies stream normally and arrive through the same `/v1/chat/completions` endpoint and the same Open WebUI conversation.

**Expected log:** the first request shows `route: general` and the prompt roles from Story 2.2 (for example `system, human`). The second shows `route: study` and the study prompt's roles, which include the earlier turns (for example `system, human, ai, human`). The question's `/study` marker is not part of what the chain receives. No keys, instruction text, or message bodies appear.

## Handover

When finished, record here:

- **Commands run:** `uv run ruff format src`, `uv run ruff check src`, and a one-off `uv run python -c` calling `_choose_route` on sample inputs.
- **Files created or changed:** `src/learning_companion/api.py` (`_choose_route`, chain selection, route label, route in dev log), `src/learning_companion/chain.py` (`describe_prompt` gets optional `study` flag), `docs/architecture.md`, this Handover.
- **Verified:** format and lint pass. `_choose_route` gives `study` for `/study`, `/study  hi there`, `/study\nx` (marker stripped; bare `/study` uses the fallback question) and `general` unchanged for `/studying x`, `hi /study x`, `/Study x`, `Hello!`.
- **Not verified:** the API was not started, so neither route was tried in Open WebUI, and no live Grok calls, label output (streaming or JSON) or log lines were observed. Steps 2–5 of the completion checks still need to be run by hand.
- **Open WebUI connection value:** unchanged from Story 1.1.

**What Story 4.1 will extend:** the same two chains, the same history conversion, and the same single chat endpoint. Story 4.1 replaces only the internal `if/else` from this story with one small LangGraph workflow: a router node that keeps the `/study` rule and writes `general` or `study` into state, two answer nodes that call the existing chains, and explicit edges to the end. It adds no review, loops, or new endpoint.
