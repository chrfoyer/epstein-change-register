"""Create an isolated git worktree for a parallel Claude Code session.

    uv run python scripts/new_session.py a feat/s1-change-classifier

Creates ../epstein-<name> on a new branch from origin/main and runs `uv sync`.
Open the new session with that directory as its working directory, then run
`/session-start <name>`. Always use the worktree's own absolute paths: editing
files under another worktree's path is how sessions collide.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(*cmd: str, cwd: Path = ROOT) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    name, branch = sys.argv[1].lower(), sys.argv[2]
    target = ROOT.parent / f"epstein-{name}"
    if target.exists():
        print(f"{target} already exists; pick another name or remove the worktree first.")
        return 1

    run("git", "fetch", "origin")
    run("git", "worktree", "add", str(target), "-b", branch, "origin/main")
    run("uv", "sync", cwd=target)
    print(f"\nReady: {target}\nBranch: {branch}\nNext: open Claude Code there and run /session-start {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
