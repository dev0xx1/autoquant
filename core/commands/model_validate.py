from __future__ import annotations

from typing import Any

from core.constants import MODELS_CSV
from core.model_runtime import validate_model_file
from core.paths import run_dir
from core.storage import get_model_map

from .shared import load_run_settings


def model_validate(run_id: str, model_id: str) -> dict[str, Any]:
    model = get_model_map(run_dir(run_id), MODELS_CSV).get(model_id)
    if model is None:
        raise RuntimeError(f"Unknown model_id={model_id}")
    settings = load_run_settings(run_id)
    validate_model_file(run_dir(run_id) / model.model_path, allowed_predictor_models=settings.available_predictor_models)
    return {"run_id": run_id, "model_id": model_id, "valid": True}
