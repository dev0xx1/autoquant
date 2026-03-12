from __future__ import annotations

from enum import Enum
import json
from pathlib import Path

from core.utils.io_util import read_csv, upsert_csv
from core.utils.metrics_util import extract_validation_metrics
from core.schemas import ExperimentRow, ModelRow, PredictionRow

def _clean_optional(value: str) -> str | None:
    return None if value == "" else value


def parse_model_rows(rows: list[dict[str, str]]) -> list[ModelRow]:
    parsed: list[ModelRow] = []
    for row in rows:
        payload = dict(row)
        payload["name"] = payload.get("name") or payload.get("model_id", "")
        payload["generation"] = int(payload.get("generation") or 0)
        payload["task"] = payload.get("task") or "classification"
        payload["model_path"] = payload.get("model_path", "")
        payload["training_size_days"] = int(payload.get("training_size_days") or 30)
        payload["test_size_days"] = int(payload.get("test_size_days") or 7)
        payload["parent_id"] = _clean_optional(payload.get("parent_id", ""))
        payload["log"] = payload.get("log", "")
        parsed.append(ModelRow.model_validate(payload))
    return parsed


def parse_experiment_rows(rows: list[dict[str, str]]) -> list[ExperimentRow]:
    parsed: list[ExperimentRow] = []
    for row in rows:
        payload = dict(row)
        payload["generation"] = int(payload.get("generation") or 0)
        payload["task"] = payload.get("task") or "classification"
        metrics_raw = payload.get("metrics", "")
        metrics = extract_validation_metrics(json.loads(metrics_raw)) if metrics_raw else None
        payload["metrics"] = metrics
        for key in ["started_at_utc", "finished_at_utc", "error"]:
            payload[key] = _clean_optional(payload.get(key, ""))
        parsed.append(ExperimentRow.model_validate(payload))
    return parsed


def parse_prediction_rows(rows: list[dict[str, str]]) -> list[PredictionRow]:
    parsed: list[PredictionRow] = []
    for row in rows:
        payload = dict(row)
        if payload.get("prediction", "").startswith("PredictionLabel."):
            payload["prediction"] = payload["prediction"].split(".", 1)[1]
        if payload.get("actual", "").startswith("PredictionLabel."):
            payload["actual"] = payload["actual"].split(".", 1)[1]
        payload["actual"] = _clean_optional(payload.get("actual", ""))
        is_correct = payload.get("is_correct", "")
        payload["is_correct"] = None if is_correct == "" else is_correct.lower() == "true"
        parsed.append(PredictionRow.model_validate(payload))
    return parsed


def _serialize(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, separators=(",", ":"), sort_keys=True)
    return str(value)


def to_dict_rows(items: list[object]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in items:
        payload = getattr(item, "model_dump")()
        rows.append({k: _serialize(v) for k, v in payload.items()})
    return rows


def get_model_rows(base_dir: Path, models_csv: str) -> list[ModelRow]:
    return parse_model_rows(read_csv(base_dir / models_csv))


def get_model_map(base_dir: Path, models_csv: str) -> dict[str, ModelRow]:
    return {m.model_id: m for m in get_model_rows(base_dir, models_csv)}


