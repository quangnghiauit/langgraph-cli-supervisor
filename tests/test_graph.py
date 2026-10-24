"""Offline checks for graph routing. Run: python3 -m unittest discover -s tests."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from orchestrator import config
from orchestrator.graph import build_graph, route_after_codex


class GraphRoutingTest(unittest.TestCase):
    def test_failed_test_retries_with_opencode_before_limit(self):
        state = {"test_result": "fail", "attempts": 2, "max_attempts": 3}
        self.assertEqual(route_after_codex(state), "opencode")

    def test_failed_test_escalates_at_limit(self):
        state = {"test_result": "fail", "attempts": 3, "max_attempts": 3}
        self.assertEqual(route_after_codex(state), "human_review")

    def test_passing_or_unknown_test_returns_to_supervisor(self):
        for result in ("pass", "unknown"):
            self.assertEqual(route_after_codex({"test_result": result}), "supervisor")

    def test_graph_has_only_documented_nodes(self):
        with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
            checkpoint_db = f.name
        previous = config.CHECKPOINT_DB
        try:
            config.CHECKPOINT_DB = checkpoint_db
            app = build_graph()
            self.assertEqual(
                set(app.get_graph().nodes),
                {"__start__", "supervisor", "claude_code", "opencode", "codex", "human_review", "__end__"},
            )
        finally:
            config.CHECKPOINT_DB = previous
            os.unlink(checkpoint_db)


if __name__ == "__main__":
    unittest.main()
