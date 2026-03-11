from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from core.schemas import Settings


def load_settings(base_dir: Path, config_path: Path | None = None) -> Settings:
    load_dotenv(base_dir / ".env")
    cfg_path = config_path or (base_dir / "config.yaml")
    raw = yaml.safe_load(cfg_path.read_text()) or {}
    if "available_predictor_models" not in raw and "predictor_model" in raw:
        raw["available_predictor_models"] = [raw["predictor_model"]]
        del raw["predictor_model"]
    settings = Settings.model_validate(raw)
    settings.prediction_time = os.getenv("AUTOQUANT_PREDICTION_TIME", settings.prediction_time)
    settings.prediction_time_timezone = os.getenv("AUTOQUANT_PREDICTION_TIME_TIMEZONE", settings.prediction_time_timezone)
    settings = Settings.model_validate(settings.model_dump(mode="json"))
    return settings
