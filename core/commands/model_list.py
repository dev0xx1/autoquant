from __future__ import annotations

from typing import Any

from core.constants import MODELS_CSV
from core.paths import run_dir
from core.utils.storage import get_model_rows


def model_list(run_id: str) -> list[dict[str, Any]]:
    return [
        row.model_dump(mode="json")
        for row in sorted(get_model_rows(run_dir(run_id), MODELS_CSV), key=lambda model: (model.generation, model.model_id))
    ]
