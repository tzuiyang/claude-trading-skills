from __future__ import annotations

from pathlib import Path

import pandas as pd
import yfinance as yf


class YFinanceClient:
    """Fetches OHLCV from yfinance with CSV disk cache."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir = cache_dir or Path(__file__).resolve().parent / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_prices(
        self,
        ticker: str,
        start: str | None = None,
        end: str | None = None,
        period: str = "5y",
    ) -> pd.DataFrame:
        cache_path = self.cache_dir / f"{ticker.upper()}.csv"

        # Try cache first
        if cache_path.exists():
            cached = pd.read_csv(cache_path, index_col=0, parse_dates=True)
            if not cached.empty:
                last_cached = cached.index.max()
                today = pd.Timestamp.now().normalize()
                if (today - last_cached).days <= 1:
                    return self._slice(cached, start, end)

        # Fetch from yfinance
        tk = yf.Ticker(ticker)
        df = tk.history(period=period, auto_adjust=False)

        if df.empty:
            raise ValueError(f"No data returned for {ticker}")

        # Normalize columns
        df.columns = [c.lower().replace(" ", "_") for c in df.columns]
        keep_cols = ["open", "high", "low", "close", "adj_close", "volume"]
        available = [c for c in keep_cols if c in df.columns]
        df = df[available]

        if "adj_close" not in df.columns and "close" in df.columns:
            df["adj_close"] = df["close"]

        df.index = pd.DatetimeIndex(df.index).tz_localize(None)
        df = df.sort_index()

        # Cache to disk as CSV
        df.to_csv(cache_path)

        return self._slice(df, start, end)

    def get_stock_info(self, ticker: str) -> dict:
        tk = yf.Ticker(ticker)
        info = tk.info or {}
        return {
            "name": info.get("longName") or info.get("shortName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "exchange": info.get("exchange"),
            "market_cap": info.get("marketCap"),
        }

    @staticmethod
    def _slice(df: pd.DataFrame, start: str | None, end: str | None) -> pd.DataFrame:
        if start:
            df = df.loc[pd.Timestamp(start):]
        if end:
            df = df.loc[:pd.Timestamp(end)]
        return df
