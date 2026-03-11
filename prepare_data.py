from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from polygon import RESTClient

from core import NEWS_CSV, PRICES_CSV
from core.constants import RUN_SETTINGS_JSON
from core.io_util import upsert_csv
from core.schemas import Settings


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
        price = _value(item, ["close", "c"])
        if ts is None or price is None:
            continue
        volume = _value(item, ["volume", "v"])
        rows.append(
            {
                "timestamp": _iso_utc(ts),
                "ticker": ticker,
                "price": str(price),
                "volume": str(volume) if volume is not None else "",
            }
        )
    return rows


def fetch_news(client: RESTClient, ticker: str, from_date: str, to_date: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in client.list_ticker_news(
        ticker=ticker,
        published_utc_gte=f"{from_date}T00:00:00Z",
        published_utc_lte=f"{to_date}T23:59:59Z",
        order="asc",
        sort="published_utc",
        limit=1000,
    ):
        ts = _iso_utc(_value(item, ["published_utc", "timestamp", "published_at"]))
        if not ts:
            continue
        dt = datetime.fromisoformat(ts).astimezone(UTC)
        rows.append(
            {
                "ticker": ticker,
                "timestamp": ts,
                "date": dt.date().isoformat(),
                "title": str(_value(item, ["title"]) or ""),
                "content": str(_value(item, ["article", "content", "description"]) or ""),
                "summary": str(_value(item, ["summary", "description"]) or ""),
                "url": str(_value(item, ["article_url", "url"]) or ""),
            }
        )
    return rows


def run_prepare_data(base_dir: Path, settings: Settings, ticker: str, from_date: str, to_date: str) -> None:
    load_dotenv(base_dir / ".env")
    load_dotenv(Path(__file__).resolve().parent / ".env")
    api_key = os.getenv("POLYGON_API_KEY")
    if not api_key:
        raise RuntimeError("POLYGON_API_KEY is required")
    client = RESTClient(api_key)
    prices = fetch_prices(client, ticker, from_date, to_date)
    news = fetch_news(client, ticker, from_date, to_date)
    prices_path = base_dir / PRICES_CSV
    news_path = base_dir / NEWS_CSV
    upsert_csv(prices_path, ["timestamp", "ticker", "price", "volume"], ["timestamp", "ticker"], prices)
    upsert_csv(
        news_path,
        ["ticker", "timestamp", "date", "title", "content", "summary", "url"],
        ["ticker", "timestamp", "url"],
        news,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--from_date", required=True)
    parser.add_argument("--to_date", required=True)
    parser.add_argument("--base_dir", default="")
    parser.add_argument("--settings_json", default="")
    args = parser.parse_args()
    target_base = Path(args.base_dir).resolve() if args.base_dir else Path(__file__).resolve().parent
    settings_path = Path(args.settings_json).resolve() if args.settings_json else (target_base / RUN_SETTINGS_JSON)
    settings = Settings.model_validate(json.loads(settings_path.read_text(encoding="utf-8")))
    run_prepare_data(target_base, settings, args.ticker, args.from_date, args.to_date)


if __name__ == "__main__":
    main()
