from __future__ import annotations

from typing import Any

from core.constants import RUN_SETTINGS_JSON
from core.graph import init_graph
from core.io_util import write_json
from core.paths import run_dir
from core.schemas import RunMeta, Settings
from core.time_utils import now_utc

from .shared import ensure_run_layout, write_run_meta


def run_init(
    run_id: str,
    ticker: str,
    from_date: str,
    to_date: str,
    available_predictor_models: list[str],
    llm_temperature: float,
    llm_max_tokens: int,
    generation_sample_size: int,
    max_experiments: int,
    max_concurrent_models: int,
    prediction_time: str,
    prediction_time_timezone: str,
    objective_function: str,
) -> dict[str, Any]:
    target_run_dir = run_dir(run_id)
    settings = Settings.model_validate(
        {
            "available_predictor_models": available_predictor_models,
            "llm_temperature": llm_temperature,
            "llm_max_tokens": llm_max_tokens,
            "generation_sample_size": generation_sample_size,
            "max_experiments": max_experiments,
            "max_concurrent_models": max_concurrent_models,
            "prediction_time": prediction_time,
            "prediction_time_timezone": prediction_time_timezone,
            "objective_function": objective_function,
        }
    )
    target_run_dir.parent.mkdir(parents=True, exist_ok=True)
    ensure_run_layout(target_run_dir)
    write_json(target_run_dir / RUN_SETTINGS_JSON, settings.model_dump(mode="json"))
    init_graph(target_run_dir)
    meta = RunMeta(
        run_id=run_id,
        ticker=ticker,
        from_date=from_date,
        to_date=to_date,
        current_generation=0,
        created_at_utc=now_utc(),
    )
    write_run_meta(meta)
    return {
        "run_id": run_id,
        "run_dir": str(target_run_dir),
        "ticker": ticker,
        "from_date": from_date,
        "to_date": to_date,
        "settings_path": str(target_run_dir / RUN_SETTINGS_JSON),
    }
