from __future__ import annotations

from typing import Any

from .generation_state import get_generation_state
from .run_metadata_get import run_metadata_get


def run_status(run_id: str) -> dict[str, Any]:
    return {
        "metadata": run_metadata_get(run_id),
        "generation": get_generation_state(run_id),
    }
