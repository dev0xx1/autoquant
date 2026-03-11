from __future__ import annotations

from pathlib import Path
from typing import Any

from .shared import load_run_settings
from core.utils.model_runtime import validate_model_file

def model_validate(run_id: str, model_path: str) -> dict[str, Any]:
    path = Path(model_path)
    if not path.exists():
        raise RuntimeError(f"File not found: {model_path}")
    settings = load_run_settings(run_id)
    validate_model_file(path, allowed_predictor_models=None, expected_task=settings.task)
    return {"run_id": run_id, "model_path": model_path, "valid": True}
