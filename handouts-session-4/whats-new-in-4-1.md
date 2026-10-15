Story 3.2 and 4.1 produce the same user-facing behavior:

- Normal messages use the general Learning Companion.
- Messages beginning with `/study` use the study helper.
- The `/study` prefix is removed before the study helper sees the question.
- Open WebUI, the API endpoint, conversation history, streaming, labels, and responses stay the same.

The difference is entirely in how the app organizes that decision internally.

| Story 3.2 | Story 4.1 |
|---|---|
| Uses a simple Python `if/else` directly in `main.py` | Uses a LangGraph workflow in a new `graph.py` |
| `main.py` decides which chain to run | `main.py` hands the request to the graph |
| Routing logic is “if `/study`, choose study chain; otherwise choose general chain” | The same logic becomes a visible workflow: `START → router → answer node → END` |
| No new dependency | Adds `langgraph` |

In plain English, 4.1 turns this:

```text
message → if/else → chosen chain → answer
```

into this:

```text
message → router → general-chat node → answer
                 └→ study-helper node → answer
```

What we are implementing in 4.1:

1. Add `langgraph` as a dependency.
2. Create `src/learning_companion/graph.py`.
3. Define a short-lived per-request state holding:
   - the latest user message,
   - recent chat history,
   - the chosen route (`general` or `study`),
   - the completed answer.
4. Create exactly three graph steps:
   - `router`: calls the existing `choose_route()` rule—still plain Python, not AI.
   - `general_chat`: runs the existing general LangChain chain.
   - `study_helper`: runs the existing study-helper LangChain chain.
5. Update `main.py` to run that graph instead of directly choosing a chain with `if/else`.
6. Keep normal and streaming Open WebUI responses identical, while development logs become more informative, e.g.:

```text
route=study | graph: START → router → study_helper → END
```

So 4.1 is a refactor for teaching workflow structure. It is not adding AI routing, agents, tools, memory, retries, loops, MCP, or a new API.