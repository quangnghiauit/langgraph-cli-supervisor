"""Daily usage tracking with per-agent limits and thresholds.

Persists a simple JSON file so limits survive across runs within the same day.
Resets automatically when the date changes.
"""
import json
import os
from datetime import date
from typing import Optional

from . import config

# Agents tracked by the usage system.
TRACKED_AGENTS = ("claude_code", "opencode", "aider")


def _load_data() -> dict:
    """Load the usage file, returning an empty structure if missing or corrupt."""
    path = config.USAGE_FILE
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_data(data: dict) -> None:
    """Persist the usage file, creating parent dirs as needed."""
    path = config.USAGE_FILE
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def _today_str() -> str:
    return date.today().isoformat()


def _get_day_entry(data: dict, today: str) -> dict:
    """Return the day's entry, resetting if the stored date differs."""
    stored_date = data.get("date", "")
    if stored_date != today:
        data.clear()
        data["date"] = today
        data["agents"] = {}
    return data


def get_count(agent: str) -> int:
    """Return today's invocation count for *agent* (0 if none recorded)."""
    data = _load_data()
    if data.get("date") != _today_str():
        return 0
    return data.get("agents", {}).get(agent, 0)


def get_limit(agent: str) -> int:
    """Return the configured daily limit for *agent* (-1 means unlimited)."""
    limits = {
        "claude_code": config.CLAUDE_DAILY_LIMIT,
        "opencode": config.OPENCODE_DAILY_LIMIT,
        "aider": config.AIDER_DAILY_LIMIT,
    }
    return limits.get(agent, -1)


def get_threshold(agent: str) -> float:
    """Return the stop-threshold (0.0–1.0) for *agent*."""
    thresholds = {
        "claude_code": config.CLAUDE_DAILY_THRESHOLD,
        "opencode": config.OPENCODE_DAILY_THRESHOLD,
        "aider": config.AIDER_DAILY_THRESHOLD,
    }
    return thresholds.get(agent, 1.0)


def get_effective_limit(agent: str) -> int:
    """Return limit × threshold, rounded down. -1 if unlimited."""
    limit = get_limit(agent)
    if limit < 0:
        return -1
    threshold = get_threshold(agent)
    return int(limit * threshold)


def is_available(agent: str) -> bool:
    """True if *agent* has not yet hit its effective daily limit."""
    effective = get_effective_limit(agent)
    if effective < 0:
        return True
    return get_count(agent) < effective


def increment(agent: str) -> int:
    """Increment today's counter for *agent* and return the new count."""
    data = _load_data()
    today = _today_str()
    day = _get_day_entry(data, today)
    agents = day.setdefault("agents", {})
    agents[agent] = agents.get(agent, 0) + 1
    _save_data(data)
    return agents[agent]


def available_agents() -> list[str]:
    """Return the subset of TRACKED_AGENTS that still have budget today."""
    return [a for a in TRACKED_AGENTS if is_available(a)]


def status() -> dict:
    """Return a summary dict suitable for logging or passing to the Supervisor."""
    result = {}
    for agent in TRACKED_AGENTS:
        count = get_count(agent)
        effective = get_effective_limit(agent)
        result[agent] = {
            "count": count,
            "limit": get_limit(agent),
            "threshold": get_threshold(agent),
            "effective_limit": effective,
            "available": is_available(agent),
        }
    return result