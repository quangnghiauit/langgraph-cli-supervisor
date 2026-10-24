"""Shared graph state passed between every node."""
from typing import TypedDict


class HistoryEntry(TypedDict):
    agent: str
    output: str
    ok: bool


class OrchestratorState(TypedDict):
    task: str
    working_dir: str

    next: str          # supervisor's routing decision: claude_code | opencode | codex | FINISH
    instructions: str  # the sub-instruction the supervisor hands to the chosen agent

    last_agent: str
    last_output: str

    test_result: str   # "pass" | "fail" | "unknown"
    attempts: int
    max_attempts: int

    history: list[HistoryEntry]
    final_summary: str
