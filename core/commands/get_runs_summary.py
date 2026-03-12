from __future__ import annotations

from pathlib import Path
from typing import Any

from core.constants import RUN_META_JSON
from core.paths import runs_root

from .shared import run_summary_for


def _is_run_dir(path: Path) -> bool:
    return path.is_dir() and (path / RUN_META_JSON).exists()


def get_runs_summary() -> dict[str, Any]:
    root_dir = runs_root()
    run_ids = sorted([path.name for path in root_dir.iterdir() if _is_run_dir(path)]) if root_dir.exists() else []
    if not run_ids:
        raise RuntimeError(f"No run directories found under {root_dir}/")
    summaries: list[dict[str, Any]] = []
    for run_id in run_ids:
        summary = run_summary_for(run_id)
        summaries.append(
            {
                "run_id": run_id,
                "last_finished_at_utc": summary["last_finished_at_utc"],
                "best_objective": summary["best_objective"],
                "objective_function": summary["objective_function"],
                "task": summary["task"],
                "n_experiments": summary["n_experiments"],
                "pending_experiments": summary["pending_experiments"],
            }
        )
    return {"runs": summaries}
