from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo


def parse_iso_to_utc(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def prediction_bounds_utc(day: str, prediction_time: str, prediction_time_timezone: str) -> tuple[datetime, datetime]:
    local_day = date.fromisoformat(day)
    hour_str, minute_str = prediction_time.split(":")
    tz = ZoneInfo(prediction_time_timezone)
    prediction_local = datetime(
        year=local_day.year,
        month=local_day.month,
        day=local_day.day,
        hour=int(hour_str),
        minute=int(minute_str),
        tzinfo=tz,
    )
    prediction_utc = prediction_local.astimezone(UTC)
    next_prediction_utc = (prediction_local + timedelta(days=1)).astimezone(UTC)
    return prediction_utc, next_prediction_utc
