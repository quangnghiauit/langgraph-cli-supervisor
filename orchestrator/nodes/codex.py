"""Codex node: generate, run, and check automated tests."""
from .. import config
from ..cli_runner import run_cli
from ..state import OrchestratorState

TEST_PROMPT_SUFFIX = (
    "\n\nRun the relevant automated tests for this change. "
    "End your final message with exactly one line: RESULT: PASS or RESULT: FAIL."
)


def codex_node(state: OrchestratorState) -> dict:
    prompt = (state["instructions"] or state["task"]) + TEST_PROMPT_SUFFIX
    result = run_cli(
        "codex",
        [
            "exec",
            prompt,
            "--sandbox",
            config.CODEX_SANDBOX_MODE,
            "--json",
        ],
        cwd=state["working_dir"],
    )

    text = result.output.upper()
    if not result.ok:
        test_result = "fail"
    elif "RESULT: FAIL" in text:
        test_result = "fail"
    elif "RESULT: PASS" in text:
        test_result = "pass"
    else:
        test_result = "unknown"

    entry = {"agent": "codex", "output": result.output, "ok": result.ok}
    attempts = state["attempts"] + 1 if test_result == "fail" else state["attempts"]
    return {
        "last_agent": "codex",
        "last_output": result.output,
        "test_result": test_result,
        "attempts": attempts,
        "history": state["history"] + [entry],
    }
