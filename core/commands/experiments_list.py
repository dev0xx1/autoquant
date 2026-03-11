from __future__ import annotations

from typing import Any

from core.constants import EXPERIMENTS_CSV
from core.paths import run_dir
from core.utils.storage import parse_experiment_rows, read_csv


def experiments_list(run_id: str, status: str | None = None) -> list[dict[str, Any]]:
    rows = parse_experiment_rows(read_csv(run_dir(run_id) / EXPERIMENTS_CSV))
    if status:
        rows = [row for row in rows if row.status == status]
    return [row.model_dump(mode="json") for row in rows]
