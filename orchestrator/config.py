"""Environment-driven configuration. No hardcoded secrets or paths."""
import os


def _env_bool(name: str, default: bool) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


TARGET_DIR = os.environ.get("AGENT_TARGET_DIR") or os.getcwd()
MAX_TEST_ATTEMPTS = int(os.environ.get("MAX_TEST_ATTEMPTS", "3"))
CHECKPOINT_DB = os.environ.get("CHECKPOINT_DB", ".checkpoints/orchestrator.sqlite")

CLAUDE_PERMISSION_MODE = os.environ.get("CLAUDE_PERMISSION_MODE", "acceptEdits")
CODEX_SANDBOX_MODE = os.environ.get("CODEX_SANDBOX_MODE", "workspace-write")
OPENCODE_AUTO_APPROVE = _env_bool("OPENCODE_AUTO_APPROVE", False)

SUPERVISOR_MODEL = os.environ.get("SUPERVISOR_MODEL")


def supervisor_llm():
    """Pick the Supervisor's LLM from whichever API key is present in the env."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=SUPERVISOR_MODEL or "claude-sonnet-5-20260101", temperature=0)
    if os.environ.get("OPENAI_API_KEY"):
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=SUPERVISOR_MODEL or "gpt-4.1", temperature=0)
    raise RuntimeError(
        "No LLM credentials found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY "
        "(see .env.example) before running the Supervisor."
    )
