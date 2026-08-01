"""OpenCode node: refactoring and large-project analysis (multi-threaded engine)."""
from .. import config
from ..cli_runner import run_cli
from ..state import OrchestratorState


def opencode_node(state: OrchestratorState) -> dict:
    prompt = state["instructions"] or state["task"]
    args = ["run", prompt, "--format", "json"]
    if config.OPENCODE_AUTO_APPROVE:
        args.append("--auto")

    result = run_cli("opencode", args, cwd=state["working_dir"])

    entry = {"agent": "opencode", "output": result.output, "ok": result.ok}
    return {
        "last_agent": "opencode",
        "last_output": result.output,
        "history": state["history"] + [entry],
    }
