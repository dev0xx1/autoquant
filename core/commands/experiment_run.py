from __future__ import annotations

from typing import Any

from core.constants import EXPERIMENTS_CSV
from core.paths import run_dir
from core.research import run_experiment
from core.storage import parse_experiment_rows, read_csv

from .shared import load_run_settings, read_run_meta


def experiment_run(run_id: str, model_id: str) -> dict[str, Any]:
    meta = read_run_meta(run_id)
    settings = load_run_settings(run_id)
    rows = parse_experiment_rows(read_csv(run_dir(run_id) / EXPERIMENTS_CSV))
    exp = next(
        (
            row
            for row in rows
            if row.model_id == model_id and row.ticker == meta.ticker and row.from_date == meta.from_date and row.to_date == meta.to_date
        ),
        None,
    )
    if exp is None:
        raise RuntimeError(f"Unknown experiment model_id={model_id} in run={run_id}")
    run_experiment(run_dir(run_id), settings, exp)
    latest = parse_experiment_rows(read_csv(run_dir(run_id) / EXPERIMENTS_CSV))
    done = next(
        row
        for row in latest
        if row.model_id == model_id and row.ticker == meta.ticker and row.from_date == meta.from_date and row.to_date == meta.to_date
    )
    return done.model_dump(mode="json")
