from __future__ import annotations

from typing import Any

from .shared import read_run_meta


def get_run_metadata(run_id: str) -> dict[str, Any]:
    return read_run_meta(run_id).model_dump(mode="json")
