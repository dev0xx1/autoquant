from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from core.model_runtime import load_model_module
from llms.call_structured import call_structured_llm
from llms.predictor.context import build_context
from core.prediction_time import parse_iso_to_utc, prediction_bounds_utc
from core.schemas import ModelRow, PredictionLabel, PredictionResponse, PredictionRow, Settings
from smartpy.utility.log_util import getLogger

logger = getLogger(__name__)


def _get_price_at_or_before(prices: list[dict[str, str]], ticker: str, ts: datetime) -> float | None:
    eligible = [p for p in prices if p["ticker"] == ticker and parse_iso_to_utc(p["timestamp"]) <= ts]
    if not eligible:
        return None
    latest = max(eligible, key=lambda x: x["timestamp"])
    return float(latest["price"])


def _get_actual_label(prices: list[dict[str, str]], ticker: str, day: str, settings: Settings) -> PredictionLabel | None:
    start, end = prediction_bounds_utc(day, settings.prediction_time, settings.prediction_time_timezone)
    p0 = _get_price_at_or_before(prices, ticker, start)
    p1 = _get_price_at_or_before(prices, ticker, end)
    if p0 is None or p1 is None:
        return None
    return PredictionLabel.UP if p1 > p0 else PredictionLabel.DOWN


def predict_one_day(
    base_dir: Path,
    settings: Settings,
    model: ModelRow,
    ticker: str,
    day: str,
    news_rows: list[dict[str, str]],
    price_rows: list[dict[str, str]],
    prediction_rows: list[dict[str, str]],
    created_at_utc: str,
) -> PredictionRow:
    logger.info("Predict start model=%s ticker=%s day=%s", model.model_id, ticker, day)
    prompt, process_prices, price_lookback_window_days, predictor_model, temperature = load_model_module(base_dir / model.model_path)
    if predictor_model not in settings.available_predictor_models:
        raise ValueError(f"predictor_model {predictor_model!r} must be one of {settings.available_predictor_models}")
    prediction_ts_utc, _ = prediction_bounds_utc(day, settings.prediction_time, settings.prediction_time_timezone)
    price_cutoff = prediction_ts_utc - timedelta(days=price_lookback_window_days)
    filtered_prices = [
        p
        for p in price_rows
        if p["ticker"] == ticker and price_cutoff <= parse_iso_to_utc(p["timestamp"]) <= prediction_ts_utc
    ]
    filtered_prices = sorted(filtered_prices, key=lambda x: x["timestamp"])
    processed_prices_raw = process_prices(filtered_prices)
    processed_prices = {k: str(v) if not isinstance(v, (str, int, float, bool, list, dict)) else v for k, v in processed_prices_raw.items()}
    context = build_context(
        news_rows=news_rows,
        price_rows=price_rows,
        prediction_rows=prediction_rows,
        ticker=ticker,
        day=day,
        model_id=model.model_id,
        settings=settings,
        processed_prices=processed_prices,
        price_lookback_window_days=price_lookback_window_days,
    )
    response = call_structured_llm(
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": json.dumps(context, ensure_ascii=True)},
        ],
        response_model=PredictionResponse,
        model=predictor_model,
        settings=settings,
        temperature=temperature,
        langfuse_name="autoquant-predictor",
        langfuse_metadata={"ticker": ticker, "day": day, "model_id": model.model_id},
    )
    actual = _get_actual_label(price_rows, ticker, day, settings)
    is_correct = None if actual is None else response.prediction == actual
    logger.info("Predict done model=%s ticker=%s day=%s prediction=%s", model.model_id, ticker, day, response.prediction.value)
    return PredictionRow(
        ticker=ticker,
        date=day,
        model_id=model.model_id,
        reasoning=response.reasoning,
        prediction=response.prediction,
        actual=actual,
        is_correct=is_correct,
        created_at_utc=created_at_utc,
    )


def get_actual_label(prices: list[dict[str, str]], ticker: str, day: str, settings: Settings) -> PredictionLabel | None:
    return _get_actual_label(prices, ticker, day, settings)
