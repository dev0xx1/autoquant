from __future__ import annotations

import shutil
from datetime import date, timedelta
from pathlib import Path

from core.constants import (
    EXPERIMENTS_CSV,
    EXPERIMENT_FIELDNAMES,
    MODEL_FIELDNAMES,
    MODELS_CSV,
    MODELS_DIR,
    NEWS_CSV,
    PREDICTIONS_CSV,
    PRICES_CSV,
    RUN_DATA_DIR,
    RUN_META_JSON,
    RUN_SETTINGS_JSON,
)
from core.io_util import ensure_csv_header, read_json, write_json
from core.paths import run_dir
from core.schemas import RunMeta, Settings
from core.storage import parse_experiment_rows, read_csv

PRICE_FETCH_LOOKBACK_DAYS = 30


def get_fetch_from_date(from_date: str) -> str:
    return (date.fromisoformat(from_date) - timedelta(days=PRICE_FETCH_LOOKBACK_DAYS)).isoformat()


def safe_model_text(source: str) -> str:
    return source.replace("\r\n", "\n").strip() + "\n"


def ensure_run_layout(target_run_dir: Path) -> None:
    (target_run_dir / RUN_DATA_DIR).mkdir(parents=True, exist_ok=True)
    (target_run_dir / MODELS_DIR).mkdir(parents=True, exist_ok=True)
    legacy_files = {
        "models.csv": MODELS_CSV,
        "experiments.csv": EXPERIMENTS_CSV,
        "predictions.csv": PREDICTIONS_CSV,
    }
    for legacy_name, target_name in legacy_files.items():
        legacy_path = target_run_dir / legacy_name
        target_path = target_run_dir / target_name
        if legacy_path.exists() and not target_path.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(legacy_path), str(target_path))
    ensure_csv_header(target_run_dir / MODELS_CSV, MODEL_FIELDNAMES)
    ensure_csv_header(target_run_dir / EXPERIMENTS_CSV, EXPERIMENT_FIELDNAMES)
    ensure_csv_header(
        target_run_dir / PREDICTIONS_CSV,
        ["ticker", "date", "model_id", "reasoning", "prediction", "actual", "is_correct", "created_at_utc"],
    )
    ensure_csv_header(target_run_dir / NEWS_CSV, ["ticker", "timestamp", "date", "title", "content", "summary", "url"])
    ensure_csv_header(target_run_dir / PRICES_CSV, ["timestamp", "ticker", "price", "volume"])


def read_run_meta(run_id: str) -> RunMeta:
    path = run_dir(run_id) / RUN_META_JSON
    if not path.exists():
        raise RuntimeError(f"Missing run metadata: {path}")
    return RunMeta.model_validate(read_json(path))


def write_run_meta(meta: RunMeta) -> None:
    write_json(run_dir(meta.run_id) / RUN_META_JSON, meta.model_dump(mode="json"))


def load_run_settings(run_id: str) -> Settings:
    path = run_dir(run_id) / RUN_SETTINGS_JSON
    if not path.exists():
        raise RuntimeError(f"Missing run settings snapshot: {path}")
    return Settings.model_validate(read_json(path))


def run_summary_for(run_id: str) -> tuple[str, str, str, str]:
    rows = parse_experiment_rows(read_csv(run_dir(run_id) / EXPERIMENTS_CSV))
    n_exp = str(len(rows))
    completed = [row for row in rows if row.status == "completed"]
    best_acc = max((row.accuracy for row in completed if row.accuracy is not None), default=None)
    best_wf1 = max((row.weighted_f1 for row in completed if row.weighted_f1 is not None), default=None)
    best_acc_s = f"{best_acc:.4f}" if best_acc is not None else "-"
    best_wf1_s = f"{best_wf1:.4f}" if best_wf1 is not None else "-"
    ts = max(((row.finished_at_utc or row.started_at_utc or "") for row in rows), default="")
    return (ts or "-", best_acc_s, best_wf1_s, n_exp)
