from __future__ import annotations

import os
from pathlib import Path

def workspace_root() -> Path:
    workspace_value = os.getenv("AUTOQUANT_WORKSPACE", "~/Documents/autoquant")
    workspace = Path(workspace_value).expanduser()
    if workspace.is_absolute():
        try:
            workspace.mkdir(parents=True, exist_ok=True)
            return workspace
        except OSError:
            pass
    fallback = Path.cwd() / "autoquant"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def runs_root() -> Path:
    root_value = os.getenv("AUTOQUANT_RUNS_ROOT", "")
    if root_value:
        root = Path(root_value).expanduser()
        if root.is_absolute():
            return root
        return Path.home() / root
    return workspace_root() / "runs"


def run_dir(run_id: str) -> Path:
    return runs_root() / run_id
