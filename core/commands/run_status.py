from __future__ import annotations

from typing import Any

from .config_get import config_get
from .generation_state import get_generation_state


def run_status(run_id: str) -> dict[str, Any]:
    return {
        "config": config_get(run_id),
        "generation": get_generation_state(run_id),
    }
