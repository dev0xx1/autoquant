from __future__ import annotations

from typing import Any

from .shared import load_run_settings, read_run_meta


def config_get(run_id: str) -> dict[str, Any]:
    meta = read_run_meta(run_id)
    settings = load_run_settings(run_id)
    payload = settings.model_dump(mode="json")
    payload.update(
        {
            "run_id": run_id,
            "ticker": meta.ticker,
            "from_date": meta.from_date,
            "to_date": meta.to_date,
            "current_generation": meta.current_generation,
        }
    )
    return payload
