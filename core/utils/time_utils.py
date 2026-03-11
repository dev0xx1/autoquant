from __future__ import annotations

from datetime import UTC, date, datetime, timedelta


def now_utc() -> str:
    return datetime.now(UTC).isoformat()


def parse_day(value: str) -> date:
    return date.fromisoformat(value)


def day_iter(from_date: str, to_date: str) -> list[str]:
    start = parse_day(from_date)
    end = parse_day(to_date)
    days: list[str] = []
    cursor = start
    while cursor <= end:
        days.append(cursor.isoformat())
        cursor += timedelta(days=1)
    return days
