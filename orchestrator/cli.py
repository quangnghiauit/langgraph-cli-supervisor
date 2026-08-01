"""CLI entrypoint: `python main.py "task description"`."""
import argparse
import sys

from langgraph.types import Command

from . import config
from .cli_runner import CliNotFoundError
from .dotenv_loader import load_dotenv
from .graph import build_graph


def _summarize(update: dict) -> str:
    parts = []
    for key in ("next", "test_result", "attempts"):
        if key in update:
            parts.append(f"{key}={update[key]}")
    if "last_output" in update:
        snippet = (update["last_output"] or "").replace("\n", " ")[:160]
        parts.append(f'output="{snippet}"')
    return ", ".join(parts) if parts else str(update)


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Claude Code / OpenCode / Codex supervisor graph")
    parser.add_argument("task", nargs="?", help="Task description for the Supervisor")
    parser.add_argument("--thread-id", default="default", help="Checkpoint thread id (for resuming)")
    parser.add_argument("--dir", dest="working_dir", default=config.TARGET_DIR, help="Target repo/dir")
    parser.add_argument(
        "--resume",
        default=None,
        help="Resume a thread paused at human_review, passing this text as guidance",
    )
    args = parser.parse_args()

    if args.resume is None and not args.task:
        parser.error("a task description is required unless --resume is used")

    app = build_graph()
    run_config = {"configurable": {"thread_id": args.thread_id}}

    if args.resume is not None:
        stream_input = Command(resume=args.resume)
    else:
        stream_input = {
            "task": args.task,
            "working_dir": args.working_dir,
            "next": "",
            "instructions": "",
            "last_agent": "",
            "last_output": "",
            "test_result": "unknown",
            "attempts": 0,
            "max_attempts": config.MAX_TEST_ATTEMPTS,
            "history": [],
            "final_summary": "",
        }

    try:
        for step in app.stream(stream_input, config=run_config, stream_mode="updates"):
            if "__interrupt__" in step:
                payload = step["__interrupt__"][0].value
                print("\n=== HUMAN REVIEW NEEDED ===")
                for k, v in payload.items():
                    print(f"{k}: {v}")
                print(
                    f'\nResume with:\n  python main.py --thread-id {args.thread_id} '
                    f'--resume "<your guidance>"\n'
                )
                return
            for node_name, update in step.items():
                print(f"[{node_name}] {_summarize(update)}")
    except (RuntimeError, CliNotFoundError) as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        sys.exit(1)

    final_state = app.get_state(run_config).values
    print("\n=== DONE ===")
    print(final_state.get("final_summary") or "(no summary)")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
