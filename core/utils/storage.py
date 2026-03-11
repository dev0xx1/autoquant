from __future__ import annotations

from enum import Enum
import json
from pathlib import Path

from core.utils.io_util import read_csv, upsert_csv, write_csv
from core.schemas import ExperimentRow, ModelRow, PredictionRow

def _clean_optional(value: str) -> str | None:
    return None if value == "" else value


def parse_model_rows(rows: list[dict[str, str]]) -> list[ModelRow]:
    parsed: list[ModelRow] = []
    for row in rows:
        payload = dict(row)
        payload["generation"] = int(payload.get("generation") or 0)
        payload["task"] = payload.get("task") or "classification"
        if "model_path" not in payload:
            payload["model_path"] = payload.get("prompt_path", "")
        payload["parent_id"] = _clean_optional(payload.get("parent_id", ""))
        payload["log"] = payload.get("log", "")
        parsed.append(ModelRow.model_validate(payload))
    return parsed


def parse_experiment_rows(rows: list[dict[str, str]]) -> list[ExperimentRow]:
    parsed: list[ExperimentRow] = []
    for row in rows:
        payload = dict(row)
        payload["generation"] = int(payload.get("generation") or payload.get("iteration") or 0)
        payload["task"] = payload.get("task") or "classification"
        metrics_raw = payload.get("metrics", "")
        metrics: dict[str, object] | None = None
        if metrics_raw:
            metrics = json.loads(metrics_raw)
        else:
            validation_legacy_keys = [
                "validation_n_samples",
                "validation_accuracy",
                "validation_precision",
                "validation_recall",
                "validation_f1",
                "validation_weighted_f1",
                "validation_macro_f1",
                "validation_y_dist",
            ]
            test_legacy_keys = [
                "test_n_samples",
                "test_accuracy",
                "test_precision",
                "test_recall",
                "test_f1",
                "test_weighted_f1",
                "test_macro_f1",
                "test_y_dist",
            ]
            validation_metrics: dict[str, object] = {}
            test_metrics: dict[str, object] = {}
            for key in validation_legacy_keys:
                value = _clean_optional(payload.get(key, ""))
                if value is not None:
                    metric_key = key.removeprefix("validation_")
                    validation_metrics[metric_key] = float(value) if metric_key != "n_samples" else int(value)
            for key in test_legacy_keys:
                value = _clean_optional(payload.get(key, ""))
                if value is not None:
                    metric_key = key.removeprefix("test_")
                    test_metrics[metric_key] = float(value) if metric_key != "n_samples" else int(value)
            if validation_metrics or test_metrics:
                metrics = {
                    "validation": validation_metrics,
                    "test": test_metrics,
                }
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
        payload = item.model_dump()  # type: ignore[attr-defined]
        rows.append({k: _serialize(v) for k, v in payload.items()})
    return rows


def get_model_rows(base_dir: Path, models_csv: str) -> list[ModelRow]:
    return parse_model_rows(read_csv(base_dir / models_csv))


def get_model_map(base_dir: Path, models_csv: str) -> dict[str, ModelRow]:
    return {m.model_id: m for m in get_model_rows(base_dir, models_csv)}


