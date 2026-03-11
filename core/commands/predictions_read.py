from __future__ import annotations

from typing import Any

from core.constants import PREDICTIONS_CSV
from core.paths import run_dir
from core.storage import parse_prediction_rows, read_csv


def predictions_read(run_id: str, model_id: str | None = None, date_from: str | None = None, date_to: str | None = None) -> list[dict[str, Any]]:
    rows = parse_prediction_rows(read_csv(run_dir(run_id) / PREDICTIONS_CSV))
    if model_id:
        rows = [row for row in rows if row.model_id == model_id]
    if date_from:
        rows = [row for row in rows if row.date >= date_from]
    if date_to:
        rows = [row for row in rows if row.date <= date_to]
    return [row.model_dump(mode="json") for row in rows]
