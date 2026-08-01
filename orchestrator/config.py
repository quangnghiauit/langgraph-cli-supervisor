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
USAGE_FILE = os.environ.get("USAGE_FILE", ".checkpoints/usage.json")

CLAUDE_PERMISSION_MODE = os.environ.get("CLAUDE_PERMISSION_MODE", "acceptEdits")
CODEX_SANDBOX_MODE = os.environ.get("CODEX_SANDBOX_MODE", "workspace-write")
OPENCODE_AUTO_APPROVE = _env_bool("OPENCODE_AUTO_APPROVE", False)

# --- Daily usage limits (per agent) ---
# -1 means unlimited.  Threshold is the fraction of the limit at which the
# agent is considered "exhausted" and the Supervisor should fall back to
# another agent.  For example, Claude Code with limit=50 and threshold=0.8
# stops being available after 40 invocations (80%), reserving 20% for
# manual use.
CLAUDE_DAILY_LIMIT = int(os.environ.get("CLAUDE_DAILY_LIMIT", "50"))
CLAUDE_DAILY_THRESHOLD = float(os.environ.get("CLAUDE_DAILY_THRESHOLD", "0.8"))

OPENCODE_DAILY_LIMIT = int(os.environ.get("OPENCODE_DAILY_LIMIT", "100"))
OPENCODE_DAILY_THRESHOLD = float(os.environ.get("OPENCODE_DAILY_THRESHOLD", "0.9"))

AIDER_DAILY_LIMIT = int(os.environ.get("AIDER_DAILY_LIMIT", "-1"))
AIDER_DAILY_THRESHOLD = float(os.environ.get("AIDER_DAILY_THRESHOLD", "1.0"))

# --- Aider configuration ---
# Aider supports many backends.  Set AIDER_MODEL to a free/cheap model such as:
#   - "deepseek/deepseek-chat" (needs DEEPSEEK_API_KEY)
#   - "openrouter/auto" or a specific free OpenRouter model (needs OPENROUTER_API_KEY)
#   - "ollama/qwen2.5-coder:7b" (needs Ollama running locally)
AIDER_MODEL = os.environ.get("AIDER_MODEL", "deepseek/deepseek-chat")
AIDER_AUTO_COMMITS = _env_bool("AIDER_AUTO_COMMITS", True)

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
