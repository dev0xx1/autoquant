from __future__ import annotations

from datetime import timedelta

from core.prediction_time import parse_iso_to_utc, prediction_bounds_utc
from core.schemas import Settings


def _price_direction(p0: float, p1: float) -> str:
    return "UP" if p1 > p0 else "DOWN"


def build_context(
    news_rows: list[dict[str, str]],
    price_rows: list[dict[str, str]],
    prediction_rows: list[dict[str, str]],
    ticker: str,
    day: str,
    model_id: str,
    settings: Settings,
    processed_prices: dict[str, object],
    price_lookback_window_days: int,
) -> dict[str, object]:
    prediction_ts_utc, _ = prediction_bounds_utc(day, settings.prediction_time, settings.prediction_time_timezone)
    news_start = prediction_ts_utc - timedelta(hours=24)
    price_start = prediction_ts_utc - timedelta(days=price_lookback_window_days)

    filtered_news = [
        n
        for n in news_rows
        if n["ticker"] == ticker and news_start <= parse_iso_to_utc(n["timestamp"]) <= prediction_ts_utc
    ]
    filtered_prices = [
        p
        for p in price_rows
        if p["ticker"] == ticker and price_start <= parse_iso_to_utc(p["timestamp"]) <= prediction_ts_utc
    ]
    filtered_news = sorted(filtered_news, key=lambda x: x["timestamp"])[-300:]
    filtered_prices = sorted(filtered_prices, key=lambda x: x["timestamp"])

    price_metrics: dict[str, object] = {}
    if filtered_prices:
        prices_float = [float(p["price"]) for p in filtered_prices]
        price_changes = [round(prices_float[i] - prices_float[i - 1], 6) for i in range(1, len(prices_float))]
        directions = [_price_direction(prices_float[i - 1], prices_float[i]) for i in range(1, len(prices_float))]
        up_count = directions.count("UP")
        down_count = directions.count("DOWN")

        volumes = []
        for p in filtered_prices:
            v = p.get("volume", "")
            if v:
                try:
                    volumes.append(float(v))
                except ValueError:
                    pass

        price_metrics = {
            "up_count": up_count,
            "down_count": down_count,
            "hourly_price_changes": price_changes[-300:],
            "hourly_directions": directions[-300:],
            "hourly_volumes": volumes[-300:] if volumes else [],
        }

    past_predictions = sorted(
        [
            {
                "date": r["date"],
                "prediction": r["prediction"],
                "actual": r.get("actual", ""),
                "is_correct": r.get("is_correct", ""),
            }
            for r in prediction_rows
            if r.get("ticker") == ticker
            and r.get("model_id") == model_id
            and r["date"] < day
        ],
        key=lambda x: x["date"],
    )[-price_lookback_window_days:]

    return {
        "ticker": ticker,
        "prediction_date_local": day,
        "prediction_timezone": settings.prediction_time_timezone,
        "prediction_time_local": settings.prediction_time,
        "prediction_timestamp_utc": prediction_ts_utc.isoformat(),
        "price_lookback_window_days": price_lookback_window_days,
        "prediction_window": {"from": news_start.isoformat(), "to": prediction_ts_utc.isoformat()},
        "task": "Predict UP or DOWN for next 24 hours.",
        "news_24h": filtered_news,
        "prices_lookback_hourly": filtered_prices[-300:],
        "processed_prices": processed_prices,
        "price_metrics": price_metrics,
        "past_predictions": past_predictions,
    }
