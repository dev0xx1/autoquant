from __future__ import annotations

from typing import Any

from core.constants import MODELS_CSV
from core.utils.io_util import read_text
from core.paths import run_dir
from core.utils.storage import get_model_map


def get_model(run_id: str, model_id: str) -> dict[str, Any]:
    model = get_model_map(run_dir(run_id), MODELS_CSV).get(model_id)
    if model is None:
        raise RuntimeError(f"Unknown model_id={model_id}")
    source = read_text(run_dir(run_id) / model.model_path)
    return {"model": model.model_dump(mode="json"), "source": source}
