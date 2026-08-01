"""Assembles the Supervisor StateGraph: nodes, conditional edges, checkpointer."""
import os
import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph

from . import config
from .nodes.claude_code import claude_code_node
from .nodes.codex import codex_node
from .nodes.human_review import human_review_node
from .nodes.opencode import opencode_node
from .nodes.supervisor import supervisor_node
from .state import OrchestratorState


def route_from_supervisor(state: OrchestratorState) -> str:
    return state["next"]


def route_after_codex(state: OrchestratorState) -> str:
    if state["test_result"] == "fail":
        if state["attempts"] >= state["max_attempts"]:
            return "human_review"
        return "opencode"
    return "supervisor"  # "pass" or "unknown" -> let the Supervisor decide next


def build_graph():
    graph = StateGraph(OrchestratorState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("claude_code", claude_code_node)
    graph.add_node("opencode", opencode_node)
    graph.add_node("codex", codex_node)
    graph.add_node("human_review", human_review_node)

    graph.set_entry_point("supervisor")

    graph.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {"claude_code": "claude_code", "opencode": "opencode", "codex": "codex", "FINISH": END},
    )
    graph.add_edge("claude_code", "supervisor")
    graph.add_edge("opencode", "codex")
    graph.add_conditional_edges(
        "codex",
        route_after_codex,
        {"supervisor": "supervisor", "opencode": "opencode", "human_review": "human_review"},
    )
    graph.add_edge("human_review", "supervisor")

    os.makedirs(os.path.dirname(config.CHECKPOINT_DB) or ".", exist_ok=True)
    conn = sqlite3.connect(config.CHECKPOINT_DB, check_same_thread=False)
    checkpointer = SqliteSaver(conn)

    return graph.compile(checkpointer=checkpointer)
