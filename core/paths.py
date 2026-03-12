from __future__ import annotations

import os
from pathlib import Path

from core.constants import TMP_DIR, TMP_MODELS_DIR, TMP_REPORTS_DIR

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
    root = workspace_root() / "runs"
    root.mkdir(parents=True, exist_ok=True)
    return root


def run_dir(run_id: str) -> Path:
    return runs_root() / run_id


def tmp_root() -> Path:
    root = workspace_root() / TMP_DIR
    root.mkdir(parents=True, exist_ok=True)
    return root


def tmp_run_dir(run_id: str) -> Path:
    root = tmp_root() / run_id
    root.mkdir(parents=True, exist_ok=True)
    return root


def tmp_models_dir(run_id: str) -> Path:
    root = tmp_run_dir(run_id) / TMP_MODELS_DIR
    root.mkdir(parents=True, exist_ok=True)
    return root


def tmp_reports_dir(run_id: str) -> Path:
    root = tmp_run_dir(run_id) / TMP_REPORTS_DIR
    root.mkdir(parents=True, exist_ok=True)
    return root
