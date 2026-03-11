from __future__ import annotations

import os
from collections import Counter
from datetime import UTC, datetime
from datetime import date as date_type
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from polygon import RESTClient

from core.constants import DATA_REPORT_TXT, NEWS_CSV, PRICES_CSV
from core.paths import run_dir
from core.schemas import Settings
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


def _coverage_stats(news: list[dict[str, str]], from_date: str, to_date: str) -> tuple[int, int, float]:
    from_day = date_type.fromisoformat(from_date)
    to_day = date_type.fromisoformat(to_date)
    total_days = (to_day - from_day).days + 1
    covered_days = len({row["date"] for row in news if row.get("date")})
    coverage_pct = (covered_days / total_days * 100) if total_days > 0 else 0.0
    return total_days, covered_days, coverage_pct


def _build_data_report(
    ticker: str,
    from_date: str,
    to_date: str,
    prices: list[dict[str, str]],
    news: list[dict[str, str]],
    total_days: int,
    covered_days: int,
    coverage_pct: float,
    min_news_coverage: float,
) -> str:
    price_day_counts = Counter(row["timestamp"][:10] for row in prices if row.get("timestamp"))
    top_price_days = sorted(price_day_counts.items(), key=lambda item: (-item[1], item[0]))[:5]
    top_price_days_text = "\n".join(f"{day}: {count}" for day, count in top_price_days) or "none"
    report_lines = [
        f"ticker: {ticker}",
        f"range_start: {from_date}",
        f"range_end: {to_date}",
        f"total_days_in_range: {total_days}",
        f"news_days_with_data: {covered_days}",
        f"news_coverage_percent: {coverage_pct:.2f}",
        f"min_news_coverage_percent: {min_news_coverage:.2f}",
        f"price_rows: {len(prices)}",
        f"price_days_with_data: {len(price_day_counts)}",
        f"news_rows: {len(news)}",
        f"generated_at_utc: {datetime.now(tz=UTC).isoformat()}",
        "top_price_days_by_row_count:",
        top_price_days_text,
    ]
    return "\n".join(report_lines) + "\n"


def run_prepare_data(base_dir: Path, settings: Settings, ticker: str, from_date: str, to_date: str) -> None:
    load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
    api_key = os.getenv("MASSIVE_API_KEY")
    if not api_key:
        raise RuntimeError("MASSIVE_API_KEY is required")
    client = RESTClient(api_key)
    prices = fetch_prices(client, ticker, from_date, to_date)
    news = fetch_news(client, ticker, from_date, to_date)
    total_days, covered_days, coverage_pct = _coverage_stats(news, from_date, to_date)
    if coverage_pct < settings.min_news_coverage:
        raise RuntimeError(
            f"News coverage {coverage_pct:.2f}% is below min_news_coverage {settings.min_news_coverage:.2f}% "
            f"({covered_days}/{total_days} days)"
        )
    prices_path = base_dir / PRICES_CSV
    news_path = base_dir / NEWS_CSV
    data_report_path = base_dir / DATA_REPORT_TXT
    upsert_csv(prices_path, ["timestamp", "ticker", "price", "volume"], ["timestamp", "ticker"], prices)
    upsert_csv(
        news_path,
        ["ticker", "timestamp", "date", "title", "content", "summary", "url"],
        ["ticker", "timestamp", "url"],
        news,
    )
    write_text(
        data_report_path,
        _build_data_report(
            ticker,
            from_date,
            to_date,
            prices,
            news,
            total_days,
            covered_days,
            coverage_pct,
            settings.min_news_coverage,
        ),
    )


def data_sync(run_id: str) -> dict[str, Any]:
    meta = read_run_meta(run_id)
    settings = load_run_settings(run_id)
    fetch_from = get_fetch_from_date(meta.from_date)
    run_prepare_data(run_dir(run_id), settings, meta.ticker, fetch_from, meta.to_date)
    return {"run_id": run_id, "ticker": meta.ticker, "fetch_from_date": fetch_from, "to_date": meta.to_date}
