from __future__ import annotations

from typing import Any

from core.paths import run_dir
from prepare_data import run_prepare_data

from .shared import get_fetch_from_date, load_run_settings, read_run_meta


def data_sync(run_id: str) -> dict[str, Any]:
    meta = read_run_meta(run_id)
    settings = load_run_settings(run_id)
    fetch_from = get_fetch_from_date(meta.from_date)
    run_prepare_data(run_dir(run_id), settings, meta.ticker, fetch_from, meta.to_date)
    return {"run_id": run_id, "ticker": meta.ticker, "fetch_from_date": fetch_from, "to_date": meta.to_date}
