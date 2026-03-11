from __future__ import annotations

from typing import Any

from core.constants import EXPERIMENTS_CSV
from core.paths import run_dir
from core.research import run_generation
from core.storage import parse_experiment_rows, read_csv

from .shared import load_run_settings, read_run_meta, write_run_meta


def generation_run(run_id: str, max_workers: int | None = None) -> dict[str, Any]:
    meta = read_run_meta(run_id)
    settings = load_run_settings(run_id)
    completed_before = len([row for row in parse_experiment_rows(read_csv(run_dir(run_id) / EXPERIMENTS_CSV)) if row.status == "completed"])
    model_ids = run_generation(run_dir(run_id), settings, meta.ticker, meta.from_date, meta.to_date, max_workers=max_workers)
    if model_ids:
        rows = parse_experiment_rows(read_csv(run_dir(run_id) / EXPERIMENTS_CSV))
        generation = max((row.generation for row in rows if row.model_id in model_ids), default=meta.current_generation)
        meta.current_generation = max(meta.current_generation, generation)
        write_run_meta(meta)
    rows_after = parse_experiment_rows(read_csv(run_dir(run_id) / EXPERIMENTS_CSV))
    completed_after = len([row for row in rows_after if row.status == "completed"])
    pending_after = len([row for row in rows_after if row.status in {"pending", "running"}])
    return {
        "run_id": run_id,
        "ran_models": model_ids,
        "completed_before": completed_before,
        "completed_after": completed_after,
        "max_experiments": settings.max_experiments,
        "pending_after": pending_after,
        "remaining_to_max": max(0, settings.max_experiments - completed_after),
    }
