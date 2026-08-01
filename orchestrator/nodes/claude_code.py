"""Claude Code node: complex source analysis and general-purpose CLI tasks."""
from .. import config
from ..cli_runner import run_cli
from ..state import OrchestratorState


def claude_code_node(state: OrchestratorState) -> dict:
    prompt = state["instructions"] or state["task"]
    result = run_cli(
        "claude",
        [
            "-p",
            prompt,
            "--output-format",
            "json",
            "--permission-mode",
            config.CLAUDE_PERMISSION_MODE,
        ],
        cwd=state["working_dir"],
    )

    entry = {"agent": "claude_code", "output": result.output, "ok": result.ok}
    return {
        "last_agent": "claude_code",
        "last_output": result.output,
        "history": state["history"] + [entry],
    }
