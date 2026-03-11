from __future__ import annotations

import os
from pathlib import Path

from core.constants import RUNS_ROOT


def runs_root() -> Path:
    root_value = os.getenv("AUTOQUANT_RUNS_ROOT", RUNS_ROOT)
    root = Path(root_value).expanduser()
    if root.is_absolute():
        return root
    return Path.home() / root


def run_dir(run_id: str) -> Path:
    return runs_root() / run_id
