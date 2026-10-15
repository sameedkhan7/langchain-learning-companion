# LangChain and LangGraph Fundamentals — Build a Practical AI Chatbot
### A four-hour, intensive lab-driven program for developers building a small, inspectable AI chatbot

**Duration:** Approximately 4 working hours / intensive half-day program, with a short break between the LangChain and LangGraph sections
**Format:** Instructor-led, lab-driven, continuous capstone project

---

## Why this course exists

Calling an LLM API from Python is straightforward. The work becomes repetitive when an application needs consistent instructions, structured messages, conversation history, reusable chains, model-provider changes, and a clear way to route a request to the right capability.

**This program gives developers a practical, build-first understanding of why LangChain exists: participants create one small LangChain-backed chatbot that they use through their working Open WebUI setup from the first session. They finish by using LangGraph to make the same chatbot follow an explicit stateful graph with simple routing between specialist agents.**

By the end of the program, participants will have built a working chatbot using Grok, seen why a direct Python implementation becomes repetitive, and used LangChain and LangGraph only where they make the application easier to read, extend, and explain.

---

## What makes this different

The application is visible from the first session. **This is an engineering room: each idea becomes a small, inspectable part of one working chatbot.** You will:

- **Start with the real chat experience** — connect the existing Open WebUI setup to a small LangChain-backed chat endpoint in the first session.
- **Build one chat experience in order** — move from a message and response to prompt templates, message history, reusable chains, and structured routing without replacing the project at each step.
- **Use LangGraph for one clear reason** — represent state, nodes, edges, and conditional routing in a small chatbot before discussing more advanced agent systems.

The course favours a clear mental model and a working project over a catalogue of framework features.

---

## Skills You'll Walk Away With

- Explain the difference between a direct LLM API call, a LangChain application flow, and a LangGraph stateful workflow.
- Configure a LangChain-backed Grok chat model behind an OpenAI-compatible chat endpoint without exposing credentials in source code.
- Build reusable chat prompts from system, user, and conversation messages instead of constructing ad-hoc strings throughout an application.
- Use LangChain model, prompt, message, and output components to create a small chatbot chain that is easier to read and change than a direct Python implementation.
- Add simple conversation history and inspect what messages are actually sent to the model.
- Explain LangGraph state, nodes, edges, conditional edges, a bounded loop, and `START`/`END` using a working graph.
- Build a deliberately small multi-agent workflow in which a router selects either a general-chat or study-helper agent, a reviewer checks the draft, and an improver revises it at most once when needed.

---

## Who should attend

This program is for developers and technical professionals who want a practical first step into LLM application frameworks.

- **Python developers** — moving from one-off LLM API calls to a small, maintainable AI application.
- **Backend developers** — learning the basic abstractions before adding LLM capability to a service or product.
- **Frontend and full-stack developers** — understanding what sits behind an AI chat interface and how its conversation flow is composed.
- **AI application beginners** — building a first chatbot with a framework rather than starting with advanced agent systems.
- **Technical leads and solution architects** — learning where LangChain and LangGraph help, and where ordinary Python remains sufficient.

*Prerequisites: comfort with Python, virtual environments or UV, environment variables, and a basic HTTP/API call. Participants need access to a Grok API key. Prior LangChain, LangGraph, AI-agent, or machine-learning experience is not required.*

---

## Course Outline

### Part 1 — Build a Clear LangChain Chatbot Foundation
*Connect a real chat interface first, then add only the LangChain components that make the application flow clearer and more reusable.*

#### Session 1 — Establish the LangChain Chatbot and Its Open WebUI Contract
*Create one small LangChain-backed chat application, connect it to Open WebUI, and make the reason for a framework concrete.*

- LLM application in one flow: Open WebUI → chat endpoint → application instructions and messages → model API → streamed answer in Open WebUI
- A direct Python call as a brief comparison: provider client, system instruction, user message, response extraction, and the responsibilities that accumulate as a chatbot grows
- Why not write everything from scratch: prompt construction, message formats, provider-specific clients, response handling, streaming, and repeated glue code grow as the chatbot grows
- What LangChain is and is not: a set of composable application abstractions, not a replacement for Python, the model provider, or sound application design
- The course capstone: one **Learning Companion Chatbot** that answers ordinary questions, remembers the short current conversation, and later routes study-help questions to a specialist
- *Hands-on:* Seed the capstone as a LangChain-backed chat service and make the first real calls through the participants' existing Open WebUI setup.
  - Create a small Python project with a `src/` application package, `tests/` directory for optional later checks, `.env.example`, `.gitignore`, `pyproject.toml`, and a concise `README.md`.
  - Add a minimal FastAPI application with `GET /health`, `GET /v1/models`, and an OpenAI-compatible `POST /v1/chat/completions` endpoint that the existing Open WebUI setup can use.
  - Add the Grok LangChain provider package and create the Grok chat model from environment-based configuration. Keep the system instruction and model name in one clear location; never place an actual API key in the repository.
  - Use a small LangChain prompt → model → text-output chain to return a Learning Companion answer through the chat endpoint. Support the normal OpenAI-compatible response shape first; add simple streaming text frames if the existing Open WebUI connection expects streaming.
  - Record the application flow in `docs/architecture.md`: Open WebUI, chat endpoint, prompt/messages, LangChain model, provider API, and answer. Briefly compare this with the direct-Python responsibilities that LangChain now organises.
  - Point the participant's already-working Open WebUI connection at the local application, select the exposed model, and run one prepared greeting and one simple study question in the chat interface.
  - **Session checkpoint:** a seeded, runnable LangChain chatbot, a connected Open WebUI chat experience, and one Grok answer returned through the application endpoint.

#### Session 2 — Compose the Chatbot with Clear LangChain Building Blocks
*Make the initial LangChain chat flow more reusable and inspectable without changing the Open WebUI chat experience.*

- LangChain's beginner building blocks: chat model, messages, prompt template, parser, and runnable chain
- Grok model configuration in plain language: keep the application flow separate from the model name and environment-based credentials
- Prompt templates: separate stable system behaviour from changing user input instead of assembling one large string
- Chains without mystery: prompt → model → output parser; inspect the input and output at each step
- Conversation history as messages: retain a short in-memory chat transcript and pass it deliberately with the next request
- *Hands-on:* Refine the initial LangChain chatbot into a small, reusable chat flow without changing its Open WebUI experience.
  - Replace the initial fixed prompt with a chat prompt containing a stable Learning Companion system message, previous messages, and the current user message.
  - Refine the prompt → model → text-output chain already used by the existing chat endpoint.
  - Maintain a small in-memory list of chat messages for the current run. Demonstrate that the chatbot can answer one follow-up question using earlier conversational context.
  - Print or log a readable development view of the prompt messages and final answer so participants can inspect what the chain is doing.
  - Compare the direct-call and LangChain versions: identify which code became reusable, and identify the simple cases where direct Python would still be enough.
  - Use the same conversation through Open WebUI and confirm that the existing chat interface continues to receive the LangChain answer.
  - **Session checkpoint:** a working LangChain chatbot with clear prompt construction, a short visible conversation history, one reusable chain, and the same connected Open WebUI experience.

#### Session 3 — Add One Useful Chatbot Capability Without Losing the Simple Flow
*Extend the same chatbot with a small, explainable distinction between ordinary chat and focused study help.*

- Instructions versus user content: keep the chatbot's role stable while allowing each request to vary
- Simple output shaping: request a concise answer plus an optional next learning step in a consistent, readable format
- Two specialist behaviours, not two applications: a general-chat instruction and a study-helper instruction over the same model and conversation
- Preparing for graph routing: the application needs to decide which behaviour should answer; a growing `if/else` block is the bridge to the next session
- *Hands-on:* Add a simple study-helper capability and make the routing decision inspectable in ordinary Python first.
  - Add a second LangChain prompt/chain for the study-helper role. It explains a beginner technical concept in plain language and suggests one small next step.
  - Keep the existing general-chat chain for greetings, general conversation, and non-study requests.
  - Implement a deliberately simple, visible Python classifier rule for prepared examples, such as `/study` selecting the study-helper path and all other messages selecting general chat.
  - Return and display the selected path with the answer so participants can see why the chatbot used that behaviour.
  - Run prepared examples through both paths and confirm that the same current conversation messages can be supplied to either specialist.
  - **Session checkpoint:** one LangChain chatbot with two small, readable behaviours and an explicit routing decision ready to be represented as a graph.

### Part 2 — Use LangGraph for Explicit Stateful Routing
*Move the existing routing decision into a small graph, so state and the path through the chatbot are visible rather than hidden in application control flow.*

#### Session 4 — Model the Chatbot as a LangGraph and Meet a Small Multi-Agent Workflow
*Build one small stateful graph with nodes, edges, conditional routing, and one bounded review loop; use specialist agents only to make the workflow understandable.*

- Why LangGraph here: an explicit model of application state and routing becomes easier to follow as a workflow gains branches, retries, review steps, or specialist agents
- Graph vocabulary in one working example: shared state, node, edge, conditional edge, `START`, and `END`
- State versus message history: state carries the current request, messages, selected route, draft answer, review result, revision count, and final answer while nodes read and update the parts they own
- Nodes are focused work, not automatically agents: the router is ordinary application logic; the general-chat, study-helper, reviewer, and improver nodes are small LLM-powered specialist behaviours
- A bounded review loop: the reviewer approves a clear draft or sends it once to the improver, then reviews the improved draft once more before the graph ends
- Multi-agent in the smallest useful sense: more than one specialist LLM behaviour coordinated by explicit routing and state, not an autonomous team with open-ended tools or unbounded loops
- When to use what: use LangChain for a straightforward model flow; use LangGraph when the visible state and controlled path between steps matter
- *Hands-on:* Rebuild the existing two-path chatbot as one small LangGraph workflow with a visible, one-time review-and-improve path.
  - Define a minimal graph state containing the current user message, current conversation messages, selected route, draft answer, review decision, revision count, and final answer.
  - Create a router node that applies the same prepared routing rule used in Session 3 and writes `general` or `study` into state.
  - Create a general-chat node and a study-helper node that call the existing LangChain chains and write a draft answer back to state.
  - Add an answer-reviewer node that makes one simple decision: approve a draft that is clear and appropriate for the selected role, or request one improvement with a short reason.
  - Add an answer-improver node that uses the reviewer’s reason to revise the draft once and increments the revision count. It does not call tools, create new plans, or loop indefinitely.
  - Add `START → router`, conditional edges from the router to the selected specialist node, and edges from both specialists to the reviewer. The reviewer either accepts the draft and ends, or sends it to the improver once; the improver returns its revised draft to the reviewer for one final approval. Permit at most one improvement before the graph ends.
  - Invoke the graph with one general-chat example and one study-help example that needs a clearer answer. Print the selected route, review decision, revision count, and final state so the path can be inspected.
  - Draw the graph beside the code and explain each node and edge in the running application: router → selected specialist → reviewer → either end or one improvement → reviewer → end.
  - **Session checkpoint:** one working Learning Companion Chatbot whose LangGraph state, router node, conditional edges, four specialist behaviours, one bounded review path, and final answer can all be explained by a participant.

---

## Capstone project

Participants incrementally build a **Learning Companion Chatbot** using the Grok model API. The capstone is deliberately small: it teaches the core reasons to use LangChain and the core graph concepts in LangGraph; it is not a production chat product or an advanced autonomous agent system.

The project has one continuous path throughout the course:

- **Open WebUI and LangChain chatbot** establish a real chat interface and a LangChain-backed OpenAI-compatible endpoint from Session 1.
- **LangChain refinement** replaces the initial fixed prompt with reusable messages, a prompt template, text output, and a small in-memory conversation history.
- **Two focused behaviours** add general chat and beginner study help through separate, readable LangChain chains.
- **LangGraph workflow** retains those chains and makes the controlled path explicit: a router node chooses one specialist agent, a reviewer approves or requests one improvement, and an improver revises once before the reviewer gives final approval and the graph ends.

The application builds in one direction. Each session extends the same OpenAI-compatible chat endpoint, Open WebUI connection, architecture note, configuration pattern, and conversation data. Participants do not replace their project with a new demo when LangGraph begins. The graph uses the LangChain chains already built, so the distinction is clear: LangChain composes model work; LangGraph controls the state and route through the work.

**In scope:** Python project setup, an OpenAI-compatible chat endpoint for the participants' existing Open WebUI setup, environment-based Grok configuration, a brief direct-LLM-call comparison, LangChain chat models, messages, prompt templates, output parsing, simple chains, short in-memory conversation history, a simple routing rule, LangGraph state, nodes, edges, conditional edges, one bounded review-and-improve path, and a four-specialist multi-agent workflow.

**Out of scope for this course:** authentication, authorization, security hardening, databases, persistent memory, production deployment, observability platforms, extensive automated testing, RAG, vector databases, web search, arbitrary tool execution, human-approval workflows, evaluation harnesses, complex cyclic agents, and open-ended multi-agent systems. These are useful follow-on topics, but they would hide the basic LangChain and LangGraph ideas this program is designed to make clear.

The required outcome is a working, explainable classroom application: participants can use Open WebUI to chat with their LangChain application, see its prompt and short conversation context, ask a general or study-help question, and inspect the LangGraph route that selected the answering specialist.

---

## A note on delivery

This four-hour program is intentionally narrow. Participants use their existing Open WebUI setup from the first session, so every capability is visible as a real chat interaction rather than only a terminal demonstration. A brief direct-Python comparison makes LangChain's value concrete, but the participant application starts as a LangChain-backed chat service. The course then builds only the LangChain abstractions that participants immediately use: messages, prompt templates, a chat model, an output parser, and simple chains.

LangGraph receives a full final session because it needs a clear contrast with the chain built earlier. The graph has one router, two answering specialists, one reviewer, one improver, explicit conditional edges, a shared state, and a single permitted improvement. This is enough to teach nodes, edges, state, a bounded loop, and the most approachable meaning of multi-agent coordination without pretending participants have built a production agent platform.

Each session balances explanation, demonstration, guided implementation, inspection, and troubleshooting. The existing Open WebUI installation acts only as the chat client; participants do not rebuild or modify it. The prepared Grok configuration keeps attention on application composition rather than provider integration differences. The future handouts can follow the same sequence: one small project-local story at a time, from the Open WebUI-connected LangChain seed through the final graph, with lightweight completion checks and no unnecessary production work.

The sequence is deliberate: first make a LangChain application work through Open WebUI; then make prompt and message work reusable; then add one understandable branching requirement; finally make that branching requirement visible as a stateful graph. Participants leave able to explain not only how to use LangChain and LangGraph, but why their small chatbot uses each one.

---

**Ready to build your first structured AI chatbot?**
*Enquire about a private cohort or a tailored delivery for your developer team.*
