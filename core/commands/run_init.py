from __future__ import annotations

from pathlib import Path
from typing import Any

from core.constants import RUN_SETTINGS_JSON
from core.graph import init_graph
from core.utils.io_util import write_json
from core.paths import run_dir
from core.schemas import RunMeta, Settings
from core.utils.time_utils import now_utc

from .model_create import model_create
from .shared import ensure_run_layout, write_run_meta

SEED_MODEL_PATH = Path(__file__).resolve().parent.parent / "seed_model.py"


def run_init(
    run_id: str,
    ticker: str,
    from_date: str,
    to_date: str,
    available_predictor_models: list[str] | None = None,
    llm_temperature: float | None = None,
    llm_max_tokens: int | None = None,
    max_experiments: int | None = None,
    max_concurrent_models: int | None = None,
    prediction_time: str | None = None,
    prediction_time_timezone: str | None = None,
    objective_function: str | None = None,
    min_news_coverage: float | None = None,
    seed_model_path: str | None = None,
) -> dict[str, Any]:
    target_run_dir = run_dir(run_id)
    defaults = Settings().model_dump(mode="json")
    settings = Settings.model_validate(
        {
            "available_predictor_models": available_predictor_models if available_predictor_models is not None else defaults["available_predictor_models"],
            "llm_temperature": llm_temperature if llm_temperature is not None else defaults["llm_temperature"],
            "llm_max_tokens": llm_max_tokens if llm_max_tokens is not None else defaults["llm_max_tokens"],
            "max_experiments": max_experiments if max_experiments is not None else defaults["max_experiments"],
            "max_concurrent_models": max_concurrent_models if max_concurrent_models is not None else defaults["max_concurrent_models"],
            "prediction_time": prediction_time if prediction_time is not None else defaults["prediction_time"],
            "prediction_time_timezone": prediction_time_timezone if prediction_time_timezone is not None else defaults["prediction_time_timezone"],
            "objective_function": objective_function if objective_function is not None else defaults["objective_function"],
            "min_news_coverage": min_news_coverage if min_news_coverage is not None else defaults["min_news_coverage"],
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
    seed_path = Path(seed_model_path) if seed_model_path else SEED_MODEL_PATH
    if not seed_path.exists():
        raise RuntimeError(f"Seed model not found: {seed_path}")
    seed_content = seed_path.read_text(encoding="utf-8")
    seed_result = model_create(
        run_id=run_id,
        name="seed",
        content=seed_content,
        log="seed model",
        reasoning="initial seed",
        generation=0,
        parent_id=None,
    )
    return {
        "run_id": run_id,
        "run_dir": str(target_run_dir),
        "ticker": ticker,
        "from_date": from_date,
        "to_date": to_date,
        "settings_path": str(target_run_dir / RUN_SETTINGS_JSON),
        "seed_model_id": seed_result["model_id"],
    }
