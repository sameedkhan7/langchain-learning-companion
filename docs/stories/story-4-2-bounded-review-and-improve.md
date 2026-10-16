# Story 4.2 — Bounded Review and Improve

## Purpose

Extend the existing three-node LangGraph with one small, visible quality step: after an answer node writes a draft, a reviewer checks it once, an improver rewrites it at most once if needed, and the graph then stops. The chatbot still looks the same in Open WebUI. This story shows a graph cycle (reviewer → improver → reviewer) that is **deliberately limited to one improvement**. It is the capstone of the course.

## What this story implements in plain English

- **The answer nodes now write a draft, not the final answer.** The router and the two answer nodes from Story 4.1 stay; they just save their text as `draft_answer`.
- **A reviewer checks the draft once against a short classroom rule.** It says `approve` or `improve` and gives one short reason. It is a small Grok-powered specialist step.
- **If the reviewer says `improve`, an improver rewrites the draft once.** It uses only the draft and the reviewer's reason. It cannot browse, use tools, make a plan, or change the route.
- **The reviewer then looks one last time and must accept.** After one improvement the graph ends, whatever the draft looks like. There is no second improvement and no retry.
- **The final answer goes to Open WebUI as before**, through the same endpoint, with the same `[route: ...]` label. In development, one short log line shows the route, the decision, the revision count, and the nodes that ran.

## Prerequisites

- Stories 1.1, 2.1, 2.2, 3.1, 3.2, and 4.1 are complete: the three routes, Grok settings, `get_chain`, `get_study_chain`, `_build_history`, the `/study` rule, the LangGraph router workflow, and the existing Open WebUI connection all work. Open WebUI must not be reinstalled, reconfigured, or modified.
- `docs/config.yaml` does not exist, so use the repository root (`langchain/`). If one appears, use the project path it configures.
- Read first: `docs/architecture.md`, Stories 1.1–4.1, `.env.example`, `src/learning_companion/graph.py` (current state and nodes), `src/learning_companion/chain.py` (both answer chains), `src/learning_companion/api.py` (the OpenAI-compatible adapter), `src/learning_companion/settings.py`.
- **No new dependencies. Do not run `uv add`.** `langgraph`, `langchain`, and `langchain-xai` are already declared.
- Preserve existing work: the three routes, request and response shapes, normal JSON replies, SSE `[DONE]` handling, the 503 configuration error, the Grok settings names, `.env.example` (unchanged), `_build_history` and `MAX_HISTORY_MESSAGES`, both answer chains and their prompts, `study_dev.py`, and everything under `handouts-session-*`.

## Words used in this story

- **Router:** ordinary Python logic. **Not an agent.** It is unchanged.
- **Answer-reviewer node** and **answer-improver node:** small LLM-powered specialist nodes. For this classroom example they may be called **specialist agents**. They each do one narrow job, use no tools, and make no choice about what to do next. The graph's edges decide what runs next.
- **General-chat** and **study-helper nodes:** as in Story 4.1.
- **Cycle:** an edge that leads back to an earlier node. Here: reviewer → improver → reviewer. It is limited by `revision_count`.
- **MCP:** an MCP tool call could be a future node. It is **not part of this story**.

## The graph state (read this before the work)

Story 4.1 had four fields: `user_message`, `messages`, `route`, `answer`. This story adds exactly five fields: `draft_answer`, `review_decision`, `review_reason`, `revision_count`, and `final_answer`. `answer` is replaced by `draft_answer` and `final_answer`, so the state has nine fields in total.

| New field | Plain English |
|-----------|---------------|
| `draft_answer` | The current answer text. An answer node writes the first draft; the improver replaces it with the rewrite. Open WebUI never sees a draft directly. |
| `review_decision` | `"approve"` or `"improve"`. Empty until the reviewer has run. Written by the reviewer each time it runs. |
| `review_reason` | One short plain-English sentence explaining the decision. It is passed to the improver and shown only in the trace as a length-limited note, never the full draft. |
| `revision_count` | How many times the improver has run: starts at `0`, becomes `1` after the one allowed improvement, and never goes higher. This number is the limit that stops the cycle. |
| `final_answer` | The answer that is sent to Open WebUI. Empty until the reviewer approves (or the limit is reached). It holds a copy of the accepted `draft_answer`. |

State still lives for one request only. Nothing is saved afterwards.

## Work to do

1. **Create `src/learning_companion/review.py`** for the two new specialist chains. Reuse the same Grok model setup as `chain.py` (the same settings, `ChatXAI`, and `ConfigurationError` check). Do not add settings and do not change `.env.example`.
   - **Reviewer chain** (`get_review_chain`): one fixed, short classroom rule in the system instruction, for example: *"Approve the draft if it is clear, correct enough for a beginner, short, and fits the role: for `general` a friendly everyday reply; for `study` a plain-language explanation with one small example if useful and exactly one next learning step. Otherwise choose improve."* The input is the selected route, the question, and the draft. The output is **structured**: a small Pydantic model with `decision: Literal["approve", "improve"]` and `reason: str` (one short sentence), produced with LangChain's structured output (`with_structured_output`). If the structured output cannot be read, treat it as `approve`, so a failure never causes extra work.
   - **Improver chain** (`get_improve_chain`): the system instruction says to rewrite the draft once, following the reviewer's reason, keeping the same role and meaning, and to return only the rewritten answer. It must not claim to research, browse, or use tools. The input is the route, the draft, and the reviewer reason; the output is plain text (`StrOutputParser`).
   - No tools, no retrieval, no planning, no routing in either chain.
2. **Extend `src/learning_companion/graph.py`.** Do not rebuild it.
   - **State:** add the five fields above to `ChatState` (`review_decision` typed `Literal["", "approve", "improve"]`, `revision_count` as `int`) and remove `answer`.
   - **Existing nodes:** `router` is unchanged. `general_chat` and `study_helper` still call `get_chain()` and `get_study_chain()` exactly as now, but write `{"draft_answer": answer}` instead of `answer`.
   - **New `answer_reviewer` node:** calls the review chain and writes `review_decision` and `review_reason`. **The limit is enforced in this node's code, not left to the model:** if `revision_count >= 1`, the node skips the model call, writes `review_decision="approve"` with a fixed reason such as "Revision limit reached; accepting the current draft.", and finishes. When the decision is `approve`, it also writes `final_answer` as a copy of `draft_answer`.
   - **New `answer_improver` node:** calls the improve chain with the route, `draft_answer`, and `review_reason`; writes the rewritten text to `draft_answer` and sets `revision_count` to `state["revision_count"] + 1`. Nothing else.
   - **Edges, written out explicitly in code:**
     - `START → router`
     - `router → general_chat` or `router → study_helper` (existing conditional edge on `route`)
     - `general_chat → answer_reviewer`
     - `study_helper → answer_reviewer`
     - `answer_reviewer → END` when `review_decision == "approve"`
     - `answer_reviewer → answer_improver` when `review_decision == "improve"` **and** `revision_count == 0` (one conditional edge reading both fields; any other case goes to `END`)
     - `answer_improver → answer_reviewer`
   - There must be no other loop, retry, planner, tool, checkpointer, or open-ended agent behaviour. Both new nodes are the only LLM-powered additions.
3. **Update `src/learning_companion/api.py`** in `chat_completions` only.
   - **Start state:** the existing fields plus `draft_answer=""`, `review_decision=""`, `review_reason=""`, `revision_count=0`, `final_answer=""`.
   - **Keep the 503 behaviour:** the existing `get_chain()` check before running the graph still covers missing Grok settings, since the new chains use the same settings.
   - **Non-streaming:** return the label plus `final_answer` in the existing JSON shape.
   - **Streaming:** keep the existing SSE shape (label chunk, content chunks, stop chunk, `[DONE]`). Because a draft may be replaced, **draft text must not be streamed to Open WebUI**. Stop forwarding model text from the answer, reviewer, and improver nodes (use `stream_mode="updates"` only). Send the `[route: ...]` label as soon as the router finishes, then, once `final_answer` is available, send it in several small content chunks (for example split on whitespace in groups of a few words), then the `stop` chunk and `[DONE]`. Mid-stream errors are still surfaced in-stream as today. In this version the answer appears after the review finishes rather than word by word as Grok writes it. That is the one visible trade-off and should be stated in the architecture note.
   - Do not add custom fields, events, or any special format for Open WebUI. Do not add a second route, endpoint, or app.
4. **Add a compact development trace.** When `APP_ENV == "development"`, log one line per request with the standard `logging` module, in the same place as the current trace, for example:
   - `route=general | review=approve | revisions=0 | nodes: router → general_chat → answer_reviewer`
   - `route=study | review=approve | revisions=1 | nodes: router → study_helper → answer_reviewer → answer_improver → answer_reviewer`
   - `review` is the last reviewer decision; `revisions` is the final `revision_count`; the node sequence is collected from the nodes that actually ran, not hard-coded. The trace must never include API keys, instruction text, full prompts, the draft or final answer, or the user's message. Do not log the reviewer's reason in full; omit it, or at most log its first 80 characters.
5. **Update `docs/architecture.md`:**
   - Replace the **Workflow graph** diagram with the full graph:

     ```
     START → router ──general──→ general_chat ─┐
                     └──study───→ study_helper ─┤
                                                ▼
                                       ┌─ answer_reviewer ──approve──→ END
                                       │        │
                                       │     improve (only if revision_count == 0)
                                       │        ▼
                                       └── answer_improver
     ```

   - Update the **state fields** table (nine fields, with plain-English meaning for the five new ones).
   - Add the **node responsibilities** for `answer_reviewer` and `answer_improver`, and state that they are small LLM-powered specialist nodes (specialist agents for this classroom example), while the router is ordinary Python and not an agent.
   - Update the **edge rules** (as listed above) and state the **one-revision limit**: the improver runs at most once, enforced by `revision_count` in code.
   - Update **Message flow** (draft → review → at most one improvement → final answer → JSON or SSE) and the note that streaming now sends the reviewed final answer after review, not token-by-token drafts.
   - Add the deliberate **scope boundary**: no tools, no MCP call (a future node could hold one), no retrieval, no web search, no planner, no extra loop or retry, no human approval, no databases or persistence, no production controls.
   - Update **Later growth** to say Story 4.2 added the bounded review path and completes the course capstone.
6. **Fill in the Handover** below when done.

### Files created or changed

`src/learning_companion/review.py` (new), `src/learning_companion/graph.py`, `src/learning_companion/api.py`, `docs/architecture.md`, `docs/stories/story-4-2-bounded-review-and-improve.md` (Handover only). `chain.py`, `settings.py`, `study_dev.py`, `.env.example`, `pyproject.toml`, and `uv.lock` stay unchanged.

### Not in this story

Databases, persistence or checkpointing, RAG, web search, tools, MCP, human approval, additional agents beyond the reviewer and improver, LLM-based routing, a second improvement or any retry, a broad test suite, production controls, observability platforms, and deployment work.

## Completion checks

Keep it small. Record the commands you actually run.

1. Format and lint: `uv run ruff format src` then `uv run ruff check src` (not `.`, which trips over the junk `__MACOSX/` files).
2. Start the API with `APP_ENV=development` on the port Open WebUI already points at: `uv run uvicorn learning_companion.api:app --host 127.0.0.1 --port 8011`.
3. In the **existing** Open WebUI, send one ordinary question the reviewer should approve directly: `Hello!`
4. In the same conversation, send one `/study` question chosen to benefit from clearer wording, for example: `/study Explain what recursion is, with a short example`. (Grok's reviewer decides, so if it approves directly, ask a vaguer, harder-to-explain question such as `/study What is a closure?` and try again, so the improve path is inspected.)
5. Confirm both final answers appear in Open WebUI, and inspect the app's terminal for the compact trace of each request.

**Expected Open WebUI results:**

- **`Hello!`:** a short, friendly reply starting with `[route: general]`. It appears after a brief pause (the review runs first), in the same chat and through the same endpoint.
- **`/study ...`:** a reply starting with `[route: study]`, then a plain-language explanation ending with exactly one suggested next learning step. This is the improved text, not the first draft. No draft text, reviewer reason, or extra labels appear in the chat.
- The connection settings are unchanged.

**Expected traces:**

- First request: `route=general | review=approve | revisions=0 | nodes: router → general_chat → answer_reviewer`
- Second request (improvement needed): `route=study | review=approve | revisions=1 | nodes: router → study_helper → answer_reviewer → answer_improver → answer_reviewer`
  - The second `answer_reviewer` always ends in `approve`, because the limit is reached. The `improver` never appears twice.
- No keys, instruction text, full prompts, or message or answer bodies appear.

**Final capstone outcome:** one Learning Companion Chatbot in the existing Open WebUI. It routes a message with plain Python, answers through a general or study Grok chain, checks the draft once, improves it at most once, and returns the final answer through one OpenAI-compatible endpoint. It is a bounded three-step quality graph with no tools, no MCP, and no unlimited self-correction.

## Handover

- **Commands run:** `uv run ruff format src` (passed); `uv run ruff check src` (passed); a one-off offline Python check of the graph with stubbed chains (passed: `router → study_helper → answer_reviewer → answer_improver → answer_reviewer`, final reviewer approved by limit).
- **Files created or changed:** `src/learning_companion/review.py` (new), `src/learning_companion/graph.py`, `src/learning_companion/api.py`, `docs/architecture.md`, this story (Handover).
- **Verified:** graph compiles; edge rules and the one-revision limit behave as designed with stubbed chains.
- **Not verified:** live Grok calls, the Open WebUI chat checks (`Hello!` and a `/study` question), the real compact trace output, streaming in Open WebUI, and mid-stream errors. These still need to be run by hand.
- **Open WebUI connection value:** unchanged from Story 1.1 (nothing touched).
