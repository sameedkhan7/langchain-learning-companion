from functools import lru_cache
from typing import Literal, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import END, START, StateGraph

from learning_companion.chain import get_chain, get_study_chain
from learning_companion.review import get_improve_chain, get_review_chain

STUDY_MARKER = "/study"
STUDY_FALLBACK_QUESTION = "What should I study first as a beginner?"


class ChatState(TypedDict):
    """Work sheet for one request. Nothing is saved after the request ends."""

    user_message: str  # the learner's current question (cleaned by the router)
    messages: list[BaseMessage]  # recent earlier chat, built by _build_history
    route: Literal["general", "study"]  # written by the router
    draft_answer: str  # current answer text: first draft, then the one rewrite
    review_decision: Literal["", "approve", "improve"]  # written by the reviewer
    review_reason: str  # one short sentence from the reviewer
    revision_count: int  # times the improver has run; 0 or 1, never higher
    final_answer: str  # the accepted answer sent to Open WebUI


def choose_route(question: str) -> tuple[Literal["general", "study"], str]:
    """Plain rule: a leading '/study' picks the study route, else general."""
    after = question[len(STUDY_MARKER) :]
    if question.startswith(STUDY_MARKER) and (not after or after[0].isspace()):
        rest = after.strip()
        return "study", rest or STUDY_FALLBACK_QUESTION
    return "general", question


def router(state: ChatState) -> dict:
    """Ordinary Python logic, not an agent."""
    route, question = choose_route(state["user_message"])
    return {"route": route, "user_message": question}


async def general_chat(state: ChatState) -> dict:
    chain = get_chain()
    answer = await chain.ainvoke(
        {"question": state["user_message"], "history": state["messages"]}
    )
    return {"draft_answer": answer}


async def study_helper(state: ChatState) -> dict:
    chain = get_study_chain()
    answer = await chain.ainvoke(
        {"question": state["user_message"], "history": state["messages"]}
    )
    return {"draft_answer": answer}


async def answer_reviewer(state: ChatState) -> dict:
    """Small Grok-powered specialist. The one-revision limit is enforced here."""
    if state["revision_count"] >= 1:
        decision, reason = (
            "approve",
            "Revision limit reached; accepting the current draft.",
        )
    else:
        try:
            result = await get_review_chain().ainvoke(
                {
                    "route": state["route"],
                    "question": state["user_message"],
                    "draft": state["draft_answer"],
                }
            )
            decision, reason = result.decision, result.reason
        except Exception:  # noqa: BLE001 - unreadable review means approve
            decision, reason = "approve", "Review could not be read; accepting."
    update: dict = {"review_decision": decision, "review_reason": reason}
    if decision == "approve":
        update["final_answer"] = state["draft_answer"]
    return update


async def answer_improver(state: ChatState) -> dict:
    """Small Grok-powered specialist: rewrites the draft once. No tools."""
    rewritten = await get_improve_chain().ainvoke(
        {
            "route": state["route"],
            "draft": state["draft_answer"],
            "reason": state["review_reason"],
        }
    )
    return {"draft_answer": rewritten, "revision_count": state["revision_count"] + 1}


def after_review(state: ChatState) -> str:
    if state["review_decision"] == "improve" and state["revision_count"] == 0:
        return "answer_improver"
    return END


def pick_answer_node(state: ChatState) -> str:
    return "study_helper" if state["route"] == "study" else "general_chat"


@lru_cache
def build_graph():
    builder = StateGraph(ChatState)
    builder.add_node("router", router)
    builder.add_node("general_chat", general_chat)
    builder.add_node("study_helper", study_helper)

    builder.add_edge(START, "router")
    builder.add_conditional_edges(
        "router", pick_answer_node, ["general_chat", "study_helper"]
    )
    builder.add_node("answer_reviewer", answer_reviewer)
    builder.add_node("answer_improver", answer_improver)
    builder.add_edge("general_chat", "answer_reviewer")
    builder.add_edge("study_helper", "answer_reviewer")
    builder.add_conditional_edges(
        "answer_reviewer", after_review, ["answer_improver", END]
    )
    builder.add_edge("answer_improver", "answer_reviewer")
    return builder.compile()
