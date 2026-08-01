"""Human-in-the-loop gate: reached only after the retry budget is exhausted."""
from langgraph.types import interrupt

from ..state import OrchestratorState


def human_review_node(state: OrchestratorState) -> dict:
    human_input = interrupt(
        {
            "reason": "Max test-fix attempts reached without a passing test run.",
            "task": state["task"],
            "last_agent": state["last_agent"],
            "last_output": state["last_output"],
            "attempts": state["attempts"],
        }
    )
    return {"instructions": str(human_input), "attempts": 0}
