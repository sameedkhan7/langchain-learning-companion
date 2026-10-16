from functools import lru_cache
from typing import Literal, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import END, START, StateGraph

from learning_companion.chain import get_chain, get_study_chain

STUDY_MARKER = "/study"
STUDY_FALLBACK_QUESTION = "What should I study first as a beginner?"


class ChatState(TypedDict):
    """Work sheet for one request. Nothing is saved after the request ends."""

    user_message: str  # the learner's current question (cleaned by the router)
    messages: list[BaseMessage]  # recent earlier chat, built by _build_history
    route: Literal["general", "study"]  # written by the router
    answer: str  # written by an answer node


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
    return {"answer": answer}


async def study_helper(state: ChatState) -> dict:
    chain = get_study_chain()
    answer = await chain.ainvoke(
        {"question": state["user_message"], "history": state["messages"]}
    )
    return {"answer": answer}


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
    builder.add_edge("general_chat", END)
    builder.add_edge("study_helper", END)
    return builder.compile()
