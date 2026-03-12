from __future__ import annotations

import pandas as pd
from sklearn.model_selection import train_test_split

from core.constants import PRICES_CSV
from core.paths import run_dir
from core.utils.io_util import read_csv

OHLCV_REQUIRED_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume")


def get_ohlcv(run_id: str, ticker: str | None = None) -> list[dict[str, str]]:
    rows = read_csv(run_dir(run_id) / PRICES_CSV)
    if ticker:
        rows = [row for row in rows if row.get("ticker") == ticker]
    return rows


def load_dataset(run_id: str) -> pd.DataFrame:
    df = pd.DataFrame(get_ohlcv(run_id))
    if df.empty:
        raise RuntimeError("No OHLCV rows found")
    missing_columns = [name for name in OHLCV_REQUIRED_COLUMNS if name not in df.columns]
    if missing_columns:
        raise RuntimeError(f"OHLCV missing columns: {','.join(missing_columns)}")
    df = df.sort_values("timestamp").reset_index(drop=True)
    for name in ["open", "high", "low", "close", "volume"]:
        df[name] = pd.to_numeric(df[name], errors="coerce")
    df = df.dropna(subset=["open", "high", "low", "close", "volume"]).reset_index(drop=True)
    if len(df) < 220:
        raise RuntimeError("Need at least 220 OHLCV rows")
    return df


def get_splits(
    df: pd.DataFrame, feature_names: list[str]
) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    if len(df) < 80:
        raise RuntimeError("Not enough rows to split")
    train_df, val_df = train_test_split(df, test_size=0.2, shuffle=False)
    train_df = train_df.reset_index(drop=True)
    val_df = val_df.reset_index(drop=True)

    if train_df["target"].nunique() < 2:
        raise RuntimeError("Train target needs both classes")

    if val_df["target"].nunique() < 2:
        raise RuntimeError("Validation target needs both classes")

    if train_df.empty or val_df.empty:
        raise RuntimeError("Invalid train/validation split")
    return (
        train_df[feature_names],
        train_df["target"],
        val_df[feature_names],
        val_df["target"],
    )
