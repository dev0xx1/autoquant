from __future__ import annotations

from pathlib import Path
from typing import Any

from core.utils.model_runtime import validate_model_file

from .shared import load_run_settings


def model_validate(run_id: str, file_path: str) -> dict[str, Any]:
    path = Path(file_path)
    if not path.exists():
        raise RuntimeError(f"File not found: {file_path}")
    settings = load_run_settings(run_id)
    validate_model_file(path, allowed_predictor_models=settings.available_predictor_models)
    return {"run_id": run_id, "file_path": file_path, "valid": True}
