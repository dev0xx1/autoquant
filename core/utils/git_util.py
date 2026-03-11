from __future__ import annotations

import subprocess
from pathlib import Path


def current_repo_commit_hash() -> str | None:
    repo_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None
