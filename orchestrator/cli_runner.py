"""Thin subprocess wrapper shared by every CLI-backed agent node."""
import shutil
import subprocess
from dataclasses import dataclass


class CliNotFoundError(RuntimeError):
    pass


@dataclass
class CliResult:
    ok: bool
    output: str


def run_cli(binary: str, args: list[str], cwd: str, timeout: int = 900) -> CliResult:
    if shutil.which(binary) is None:
        raise CliNotFoundError(
            f"'{binary}' not found in PATH. Install it before running this node."
        )
    try:
        proc = subprocess.run(
            [binary, *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return CliResult(ok=False, output=f"Timed out after {timeout}s: {exc}")

    output = proc.stdout.strip() or proc.stderr.strip()
    return CliResult(ok=proc.returncode == 0, output=output)
