from __future__ import annotations

from enum import Enum
from pathlib import Path

from core.io_util import read_csv, upsert_csv, write_csv
from core.schemas import ExperimentRow, ModelRow, PredictionRow

def _clean_optional(value: str) -> str | None:
    return None if value == "" else value


def parse_model_rows(rows: list[dict[str, str]]) -> list[ModelRow]:
    parsed: list[ModelRow] = []
    for row in rows:
        payload = dict(row)
        payload["generation"] = int(payload.get("generation") or 0)
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
        for key in ["n_samples", "accuracy", "precision", "recall", "f1", "weighted_f1", "macro_f1", "y_dist"]:
            payload[key] = _clean_optional(payload.get(key, ""))
        for key in ["started_at_utc", "finished_at_utc", "error"]:
            payload[key] = payload.get(key, "")
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


