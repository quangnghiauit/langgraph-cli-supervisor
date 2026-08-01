"""Aider node: free fallback agent for refactoring and code changes.

Uses Aider's headless mode (--message + --yes-always) so it can run
non-interactively inside the graph.  Aider supports many backends including
free/cheap models via OpenRouter, DeepSeek, or local Ollama.
"""
from .. import config
from ..cli_runner import run_cli
from ..state import OrchestratorState
from ..usage_tracker import increment


def aider_node(state: OrchestratorState) -> dict:
    prompt = state["instructions"] or state["task"]
    args = [
        "--message", prompt,
        "--yes-always",
        "--no-pretty",
        "--no-stream",
        "--model", config.AIDER_MODEL,
    ]
    # Aider auto-commits by default; keep that so changes are traceable.
    if not config.AIDER_AUTO_COMMITS:
        args.append("--no-auto-commits")

    result = run_cli("aider", args, cwd=state["working_dir"])
    increment("aider")

    entry = {"agent": "aider", "output": result.output, "ok": result.ok}
    return {
        "last_agent": "aider",
        "last_output": result.output,
        "history": state["history"] + [entry],
    }