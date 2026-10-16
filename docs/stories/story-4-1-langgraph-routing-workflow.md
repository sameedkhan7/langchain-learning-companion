# Story 4.1 — LangGraph Routing Workflow

## Purpose

Replace the plain Python `if/else` from Story 3.2 with one small LangGraph workflow, so the route, the state, the steps, and the connections between them are visible in code. The chatbot behaves exactly as before. Only the way the app organises the decision changes. Story 4.2 will add a bounded review step to this graph.

## What this story implements in plain English

After this story, a question that enters the chatbot goes through these steps:

- **The app writes the question on a small "work sheet" for this one request.** The sheet holds the question, the recent chat, the chosen path, and the answer. It is thrown away when the request ends.
- **A router step reads the question and picks a path.** If the message starts with `/study`, the path is `study`. Otherwise it is `general`. This is the same plain rule as Story 3.2. No AI makes this choice.
- **One answer step runs, depending on the path.** The general-chat step asks Grok with the everyday chat instructions. The study-helper step asks Grok with the study instructions. Each one writes its answer on the work sheet.
- **The answer leaves the graph and goes back through the existing chat endpoint.** Open WebUI shows it exactly as before: normal JSON, or streamed word by word, with the `[route: ...]` label.
- **In development, one short log line shows what happened**, for example `route=study | nodes: router → study_helper`. It never shows keys, hidden instructions, or message text.

## Prerequisites

- Stories 1.1, 2.1, 2.2, 3.1, and 3.2 are complete: the three routes, Grok settings, `get_chain`, `get_study_chain`, `_build_history`, the `/study` rule, and the existing Open WebUI connection all work. Open WebUI must not be reinstalled, reconfigured, or modified.
- `docs/config.yaml` does not exist, so use the repository root (`langchain/`). If one appears, use the project path it configures.
- Read first: `docs/architecture.md`, Stories 1.1–3.2, `.env.example`, `src/learning_companion/chain.py`, `src/learning_companion/api.py` (the OpenAI-compatible chat adapter), `src/learning_companion/settings.py`.
- LangGraph is already installed as a dependency of `langchain` (`langgraph` 1.2.15 in `uv.lock`), but it is not declared in `pyproject.toml`. This story declares it with `uv add langgraph`. That is the only dependency change.
- Preserve existing work: the three routes, request and response shapes, SSE `[DONE]` handling, the 503 configuration error, the settings names, `.env.example` (unchanged), `_build_history` and `MAX_HISTORY_MESSAGES`, both chains and their prompts, `study_dev.py`, and everything under `handouts-session-*`.

## Words used in this story

- **Graph:** a small map of work steps and the arrows between them.
- **Node:** one focused piece of work in the graph. A node is **not automatically an agent**. It can be an ordinary Python function.
- **Router node:** ordinary application logic, **not an agent**. It uses the same plain `/study` rule as before.
- **General-chat node** and **study-helper node:** each calls one existing LangChain chain, so they may be described as small specialist behaviours. They do not choose their own actions and use no tools.
- **Edge:** an arrow saying which node runs next. A **conditional edge** picks one of several arrows based on the state.
- **MCP:** a tool call could be placed inside a future node, but MCP is **not implemented** in this course story.

## The graph state (read this before the work)

The state is a small typed dictionary that every node reads and updates. Define it with four fields:

| Field | Plain English |
|-------|---------------|
| `user_message` | The learner's current question. The router may remove a leading `/study` from it, so the answer nodes receive the clean question. |
| `messages` | The recent chat before this question: up to 6 earlier user and assistant messages, in order, built by the existing `_build_history`. Earlier messages are never rewritten. |
| `route` | `"general"` or `"study"`. Empty until the router writes it. |
| `answer` | The final answer text. Empty until an answer node writes it. |

The state lives only for one request. Nothing is saved afterwards.

## Work to do

1. **Declare the dependency.** Run `uv add langgraph`. It should change only `pyproject.toml` and `uv.lock`. No other package is added.
2. **Create `src/learning_companion/graph.py`** with one small graph:
   - **State:** a `TypedDict` named for example `ChatState`, with exactly the four fields above (`user_message`, `messages`, `route`, `answer`). `route` is typed `Literal["general", "study"]`.
   - **Router node, `router`:** reads `user_message`, applies the existing `/study` rule, and writes `route` plus the cleaned `user_message`. Move the rule from `api.py` into this module, or import it from there. Do **not** copy it into a second version. Keep it exactly as in Story 3.2:
     - `/study` alone, or `/study` followed by whitespace, means `study`. The match is case-sensitive and checked on the trimmed message. Only the leading marker and its surrounding whitespace are removed.
     - A bare `/study` becomes the fixed fallback question "What should I study first as a beginner?".
     - `/studying` and a `/study` in the middle of a sentence are `general`, unchanged.
     - No model call, no regex framework, no scoring, no setting.
   - **General-chat node, `general_chat`:** calls the existing `get_chain()` with `{"question": user_message, "history": messages}` and writes `answer`.
   - **Study-helper node, `study_helper`:** calls the existing `get_study_chain()` the same way and writes `answer`.
   - **Edges, written out explicitly in code:**
     - `START → router`
     - `router → general_chat` or `router → study_helper`, using one conditional edge that reads `route` from the state
     - `general_chat → END`
     - `study_helper → END`
   - Expose one compiled graph (for example `build_graph()` or a module-level `graph`). It has no reviewer, no improver, no loop, no retry, and no checkpointer. Story 4.2 adds the bounded review path.
   - Do not create new chains or prompts. Do not touch Grok settings.
3. **Make `api.py` hand the request to the graph.** In `chat_completions` only:
   - Keep `_build_history`, the `Message` and `ChatRequest` models, `_sse`, the completion id, the label, and the response shapes. Build the starting state from the latest question and history.
   - Remove the internal `if/else` chain selection and the old `_choose_route` call. Nothing else is replaced. Do not add a second route, a second endpoint, or a second app.
   - **Keep the 503 behaviour.** A missing `GROK_API_KEY` or `GROK_MODEL_NAME` must still give the same HTTP 503 message before any streaming starts. Do this by calling the existing `get_chain()` once before running the graph, inside the current `try/except ConfigurationError`. Both getters check the same settings, so this is enough, and no extra setting or helper is needed.
   - **Non-streaming:** run the graph once, then return the label plus `answer` in the existing JSON shape. The route comes from the final state, so the label is `[route: general]` or `[route: study]` as before.
   - **Streaming:** keep the existing SSE shape. Stream the graph with LangGraph's message streaming (`stream_mode="messages"`), so Grok's text pieces still reach Open WebUI as they are produced. Send the label as the first `content` delta, then each text piece, then the final `stop` chunk and `[DONE]`. The route for the label is known from the router node's update (also available through `stream_mode="updates"`, or by streaming both modes together). If an upstream error happens mid-stream, surface it in-stream exactly as today. Do not buffer the whole answer and send it as one chunk.
   - Do not add custom fields, events, or any special format for Open WebUI.
4. **Add a compact development trace.** When `APP_ENV == "development"`, log one line per chat request with the standard `logging` module, in the same place as the current development log. It shows the route and the node sequence, for example `route=study | nodes: router → study_helper`, and may keep the existing prompt-role summary on the same line or beside it. It must never include API keys, the instruction text, message text, or full prompts. The sequence is collected from the nodes that actually ran (for example from the streamed updates), not hard-coded.
5. **Update `docs/architecture.md`:**
   - Add a **Workflow graph** section with this diagram:

     ```
     START → router ──general──→ general_chat → END
                     └──study───→ study_helper → END
     ```

   - List the four **state fields** and what each one means.
   - List the **node responsibilities** (router, general-chat, study-helper) and say that a node is not automatically an agent.
   - State the **edge rules**: `START → router`; one conditional edge from `router` based on `route`; each answer node goes to `END`.
   - Update **Message flow**: request → latest user message and history built → graph (router → one answer node) → text with route label → JSON or SSE.
   - Replace the Story 3.2 sentence about "one plain Python `if`/`else`" with the graph, while keeping the `/study` rule text unchanged. The router is still deterministic application logic, not LLM classification or an agent.
   - State **what remains out of scope**: review or improve steps, loops, retries, additional agents, tools, MCP, RAG, web search, databases, persistence, human approval, and production concerns.
   - Update **Stack** to mention `langgraph`, and **Later growth** to say Story 4.2 adds the bounded review path.
6. **Fill in the Handover** below when done.

### Files created or changed

`src/learning_companion/graph.py` (new), `src/learning_companion/api.py`, `docs/architecture.md`, `pyproject.toml` and `uv.lock` (the `langgraph` declaration only), `docs/stories/story-4-1-langgraph-routing-workflow.md` (Handover only). `chain.py`, `settings.py`, `study_dev.py`, and `.env.example` stay unchanged, apart from a tiny import-only tweak to `chain.py` if one is truly needed.

### Not in this story

A reviewer, improver, loop, or retry (Story 4.2), LLM-based routing, additional agents, tool execution, MCP, RAG, web search, databases, persistence or checkpointing, human approval, a second app, endpoint, or UI, custom Open WebUI response formats, a broad test suite, security programmes, observability platforms, and deployment work.

## Completion checks

Keep it small. Record the commands you actually run.

1. Format and lint: `uv run ruff format src` then `uv run ruff check src` (not `.`, which trips over the junk `__MACOSX/` files).
2. Start the API with `APP_ENV=development` on the port Open WebUI already points at: `uv run uvicorn learning_companion.api:app --host 127.0.0.1 --port 8011`.
3. In the **existing** Open WebUI, in one conversation, send a general question: `Hello!`
4. In the same conversation, send: `/study Explain what an API is`
5. Confirm both final answers appear in Open WebUI, and inspect the app's terminal for the compact trace of each request.

**Expected Open WebUI results** (same as Story 3.2):

- **General message:** a short, friendly reply that starts with `[route: general]`, streamed normally.
- **`/study Explain what an API is`:** a reply that starts with `[route: study]`, then a plain-language explanation ending with exactly one suggested next learning step, streamed normally.
- Both arrive through the same `/v1/chat/completions` endpoint and the same conversation. The connection settings are unchanged.

**Expected trace:**

- First request: `route=general | nodes: router → general_chat`
- Second request: `route=study | nodes: router → study_helper`
- No keys, instruction text, or message bodies appear.

## Handover

When finished, record here:

- **Commands run:** `uv add langgraph` (pass; changed `pyproject.toml` and `uv.lock` only); `uv run ruff format src` (pass); `uv run ruff check src` (pass); a local FastAPI `TestClient` script with a fake chat model (pass).
- **Files created or changed:** `src/learning_companion/graph.py` (new), `src/learning_companion/api.py`, `docs/architecture.md`, `pyproject.toml`, `uv.lock`, this story (Handover). `chain.py`, `settings.py`, `.env.example` unchanged.
- **Verified:** with a fake model, general and `/study` requests both streamed (label first, then text pieces, stop, `[DONE]`); the non-streaming JSON reply carried the right label; the trace lines were `route=general | nodes: router → general_chat` and `route=study | nodes: router → study_helper`; `/study` rule cases (bare, `/studying`, normal) behave as before.
- **Not verified:** the real Grok model and the existing Open WebUI (no `GROK_API_KEY` in this environment, so the real check in Completion checks steps 2–5 still needs to be run), a mid-stream error. The missing-key 503 was observed and keeps its message.
- **Open WebUI connection value:** unchanged from Story 1.1.

**What Story 4.2 will extend:** this same graph. Story 4.2 adds one bounded review path after an answer node: a reviewer checks the draft, an improver rewrites it at most once if needed, and the graph then ends. It keeps the router, the two answer nodes, the single endpoint, and the Open WebUI connection, and it adds no loop without a limit, no tools, and no MCP.
