from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from polygon import RESTClient

from core.constants import DATA_REPORT_TXT, PRICES_CSV
from core.paths import run_dir
from core.utils.io_util import upsert_csv, write_text

from .shared import get_fetch_from_date, load_run_settings, read_run_meta


def _value(item: Any, keys: list[str]) -> Any:
    for key in keys:
        if isinstance(item, dict) and key in item:
            return item[key]
        if hasattr(item, key):
            return getattr(item, key)
    return None


def _iso_utc(ts: Any) -> str:
    if ts is None:
        return ""
    if isinstance(ts, (int, float)):
        if ts > 10_000_000_000:
            ts = ts / 1000
        return datetime.fromtimestamp(ts, tz=UTC).isoformat()
    text = str(ts).replace("Z", "+00:00")
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).isoformat()


def fetch_prices(client: RESTClient, ticker: str, from_date: str, to_date: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in client.list_aggs(
        ticker=ticker,
        multiplier=1,
        timespan="hour",
        from_=from_date,
        to=to_date,
        limit=50000,
    ):
        ts = _value(item, ["timestamp", "t"])
        open_price = _value(item, ["open", "o"])
        high_price = _value(item, ["high", "h"])
        low_price = _value(item, ["low", "l"])
        close_price = _value(item, ["close", "c"])
        if ts is None or open_price is None or high_price is None or low_price is None or close_price is None:
            continue
        volume = _value(item, ["volume", "v"])
        rows.append(
            {
                "timestamp": _iso_utc(ts),
                "ticker": ticker,
                "open": str(open_price),
                "high": str(high_price),
                "low": str(low_price),
                "close": str(close_price),
                "volume": str(volume) if volume is not None else "",
            }
        )
    return rows


def _build_data_report(
    ticker: str,
    from_date: str,
    to_date: str,
    prices: list[dict[str, str]],
) -> str:
    price_day_counts: dict[str, int] = {}
    for row in prices:
        ts = row.get("timestamp", "")
        if not ts:
            continue
        day = ts[:10]
        price_day_counts[day] = price_day_counts.get(day, 0) + 1
    top_price_days = sorted(price_day_counts.items(), key=lambda item: (-item[1], item[0]))[:5]
    top_price_days_text = "\n".join(f"{day}: {count}" for day, count in top_price_days) or "none"
    report_lines = [
        f"ticker: {ticker}",
        f"range_start: {from_date}",
        f"range_end: {to_date}",
        f"price_rows: {len(prices)}",
        f"price_days_with_data: {len(price_day_counts)}",
        f"generated_at_utc: {datetime.now(tz=UTC).isoformat()}",
        "top_price_days_by_row_count:",
        top_price_days_text,
    ]
    return "\n".join(report_lines) + "\n"


def run_prepare_data(base_dir: Path, ticker: str, from_date: str, to_date: str) -> None:
    load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
    api_key = os.getenv("MASSIVE_API_KEY")
    if not api_key:
        raise RuntimeError("MASSIVE_API_KEY is required")
    client = RESTClient(api_key)
    prices = fetch_prices(client, ticker, from_date, to_date)
    prices_path = base_dir / PRICES_CSV
    data_report_path = base_dir / DATA_REPORT_TXT
    upsert_csv(prices_path, ["timestamp", "ticker", "open", "high", "low", "close", "volume"], ["timestamp", "ticker"], prices)
    write_text(
        data_report_path,
        _build_data_report(
            ticker,
            from_date,
            to_date,
            prices,
        ),
    )


def prepare_data(run_id: str) -> dict[str, Any]:
    meta = read_run_meta(run_id)
    load_run_settings(run_id)
    fetch_from = get_fetch_from_date(meta.from_date)
    run_prepare_data(run_dir(run_id), meta.ticker, fetch_from, meta.to_date)
    return {"run_id": run_id, "ticker": meta.ticker, "fetch_from_date": fetch_from, "to_date": meta.to_date}
