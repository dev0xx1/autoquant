from __future__ import annotations

from typing import Any

from core.paths import runs_root

from .shared import run_summary_for


def runs_summary() -> dict[str, Any]:
    root_dir = runs_root()
    run_ids = sorted([path.name for path in root_dir.iterdir() if path.is_dir()]) if root_dir.exists() else []
    if not run_ids:
        raise RuntimeError(f"No run directories found under {root_dir}/")
    for idx, run_id in enumerate(run_ids, 1):
        ts, acc, wf1, n_exp = run_summary_for(run_id)
        print(f"{idx}. {run_id}  last={ts}  best_acc={acc}  best_wf1={wf1}  n_exp={n_exp}")
    choice = input("Enter number (or Enter to exit): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(run_ids):
        run_id = run_ids[int(choice) - 1]
        ts, acc, wf1, n_exp = run_summary_for(run_id)
        print(f"Run: {run_id}\nLast run: {ts}\nBest accuracy: {acc}\nBest weighted f1: {wf1}\nN experiments: {n_exp}")
    return {"ok": True}
