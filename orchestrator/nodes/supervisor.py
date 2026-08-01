"""Supervisor node: the central brain that reads state and routes to a specialist."""
from typing import Literal

from pydantic import BaseModel, Field

from .. import config
from ..state import OrchestratorState

ROUTES = ("claude_code", "opencode", "codex", "FINISH")

SYSTEM_PROMPT = """You are the Supervisor of a coding-agent pipeline. You route work \
between three specialist CLI agents operating on a local repository:

- claude_code: deep analysis of complex source code; general-purpose CLI/file tasks.
- opencode: large-scale refactoring and multi-file project analysis.
- codex: generates, runs, and checks automated tests.

Given the task, the last agent that ran, its output, and the latest test result, decide \
which specialist should act next, and write the specific instruction they should follow. \
Route to FINISH once the task is complete and tests pass (or there is nothing left to do).

Do not route to "codex" twice in a row without another agent acting in between, unless no \
other agent has run yet."""


class SupervisorDecision(BaseModel):
    next: Literal["claude_code", "opencode", "codex", "FINISH"] = Field(
        description="Which node should run next."
    )
    instructions: str = Field(
        default="", description="The concrete instruction for the chosen agent. Empty if FINISH."
    )
    summary: str = Field(
        default="", description="One-line status summary for a human watching the run."
    )


def supervisor_node(state: OrchestratorState) -> dict:
    llm = config.supervisor_llm().with_structured_output(SupervisorDecision)

    context = (
        f"Task: {state['task']}\n"
        f"Last agent: {state.get('last_agent') or 'none'}\n"
        f"Last output: {(state.get('last_output') or '')[:4000]}\n"
        f"Test result: {state.get('test_result') or 'unknown'}\n"
        f"Attempt: {state.get('attempts', 0)} / {state.get('max_attempts', config.MAX_TEST_ATTEMPTS)}\n"
    )

    decision: SupervisorDecision = llm.invoke(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": context},
        ]
    )

    return {
        "next": decision.next,
        "instructions": decision.instructions,
        "final_summary": decision.summary,
    }
