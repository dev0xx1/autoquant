from __future__ import annotations

from typing import Any

from core.paths import run_dir
from core.research import get_pending_experiments

from .shared import read_run_meta


def get_generation_state(run_id: str) -> dict[str, Any]:
    meta = read_run_meta(run_id)
    pending = get_pending_experiments(run_dir(run_id), meta.ticker, meta.from_date, meta.to_date)
    grouped: dict[int, int] = {}
    for exp in pending:
        grouped[exp.generation] = grouped.get(exp.generation, 0) + 1
    return {"run_id": run_id, "current_generation": meta.current_generation, "pending_by_generation": grouped}
