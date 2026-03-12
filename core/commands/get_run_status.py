from __future__ import annotations

from typing import Any

from .get_generation_summary import get_generation_summary
from .get_run_metadata import get_run_metadata


def get_run_status(run_id: str) -> dict[str, Any]:
    return {
        "metadata": get_run_metadata(run_id),
        "generation": get_generation_summary(run_id),
    }
