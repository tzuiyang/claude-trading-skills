from __future__ import annotations

import re

import numpy as np
import pandas as pd


class FeatureEngineer:
    """Computes technical indicators on OHLCV DataFrames.

    Feature naming convention: {indicator}_{param} — e.g. sma_20, rsi_14, ema_12.
    Only computes features listed in feature_names to minimize waste.
    """

    _PARSERS = {
        r"^sma_(\d+)$": "_sma",
        r"^ema_(\d+)$": "_ema",
        r"^rsi_(\d+)$": "_rsi",
        r"^atr_(\d+)$": "_atr",
        r"^volume_ratio_(\d+)$": "_volume_ratio",
        r"^bb_upper_(\d+)_([\d.]+)$": "_bb_upper",
        r"^bb_lower_(\d+)_([\d.]+)$": "_bb_lower",
        r"^bb_mid_(\d+)_([\d.]+)$": "_bb_mid",
        r"^macd_(\d+)_(\d+)_(\d+)$": "_macd_line",
        r"^macd_signal_(\d+)_(\d+)_(\d+)$": "_macd_signal",
        r"^macd_hist_(\d+)_(\d+)_(\d+)$": "_macd_hist",
        r"^daily_return$": "_daily_return",
        r"^high_(\d+)d$": "_rolling_high",
        r"^low_(\d+)d$": "_rolling_low",
    }

    def compute(self, df: pd.DataFrame, feature_names: list[str]) -> pd.DataFrame:
        df = df.copy()
        for name in feature_names:
            if name in df.columns:
                continue
            matched = False
            for pattern, method_name in self._PARSERS.items():
                m = re.match(pattern, name)
                if m:
                    method = getattr(self, method_name)
                    args = [self._convert_arg(a) for a in m.groups()]
                    df[name] = method(df, *args)
                    matched = True
                    break
            if not matched:
                known = list(self._PARSERS.keys())
                raise KeyError(
                    f"Unknown feature '{name}'. Known patterns: {known}"
                )
        return df

    @staticmethod
    def _convert_arg(val: str) -> int | float:
        try:
            return int(val)
        except ValueError:
            return float(val)

    @staticmethod
    def _sma(df: pd.DataFrame, window: int) -> pd.Series:
        return df["close"].rolling(window=window, min_periods=window).mean()

    @staticmethod
    def _ema(df: pd.DataFrame, window: int) -> pd.Series:
        return df["close"].ewm(span=window, adjust=False, min_periods=window).mean()

    @staticmethod
    def _rsi(df: pd.DataFrame, period: int) -> pd.Series:
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.ewm(com=period - 1, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(com=period - 1, min_periods=period, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        return 100.0 - (100.0 / (1.0 + rs))

    @staticmethod
    def _atr(df: pd.DataFrame, period: int) -> pd.Series:
        high_low = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift(1)).abs()
        low_close = (df["low"] - df["close"].shift(1)).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(window=period, min_periods=period).mean()

    @staticmethod
    def _volume_ratio(df: pd.DataFrame, window: int) -> pd.Series:
        avg_vol = df["volume"].rolling(window=window, min_periods=window).mean()
        return df["volume"] / avg_vol.replace(0, np.nan)

    @staticmethod
    def _bb_upper(df: pd.DataFrame, window: int, num_std: float) -> pd.Series:
        mid = df["close"].rolling(window=window, min_periods=window).mean()
        std = df["close"].rolling(window=window, min_periods=window).std()
        return mid + num_std * std

    @staticmethod
    def _bb_lower(df: pd.DataFrame, window: int, num_std: float) -> pd.Series:
        mid = df["close"].rolling(window=window, min_periods=window).mean()
        std = df["close"].rolling(window=window, min_periods=window).std()
        return mid - num_std * std

    @staticmethod
    def _bb_mid(df: pd.DataFrame, window: int, _num_std: float) -> pd.Series:
        return df["close"].rolling(window=window, min_periods=window).mean()

    @staticmethod
    def _macd_line(df: pd.DataFrame, fast: int, slow: int, _signal: int) -> pd.Series:
        ema_fast = df["close"].ewm(span=fast, adjust=False, min_periods=fast).mean()
        ema_slow = df["close"].ewm(span=slow, adjust=False, min_periods=slow).mean()
        return ema_fast - ema_slow

    @staticmethod
    def _macd_signal(df: pd.DataFrame, fast: int, slow: int, signal: int) -> pd.Series:
        ema_fast = df["close"].ewm(span=fast, adjust=False, min_periods=fast).mean()
        ema_slow = df["close"].ewm(span=slow, adjust=False, min_periods=slow).mean()
        macd = ema_fast - ema_slow
        return macd.ewm(span=signal, adjust=False, min_periods=signal).mean()

    @staticmethod
    def _macd_hist(df: pd.DataFrame, fast: int, slow: int, signal: int) -> pd.Series:
        ema_fast = df["close"].ewm(span=fast, adjust=False, min_periods=fast).mean()
        ema_slow = df["close"].ewm(span=slow, adjust=False, min_periods=slow).mean()
        macd = ema_fast - ema_slow
        sig = macd.ewm(span=signal, adjust=False, min_periods=signal).mean()
        return macd - sig

    @staticmethod
    def _daily_return(df: pd.DataFrame) -> pd.Series:
        return df["close"].pct_change()

    @staticmethod
    def _rolling_high(df: pd.DataFrame, window: int) -> pd.Series:
        return df["high"].rolling(window=window, min_periods=window).max()

    @staticmethod
    def _rolling_low(df: pd.DataFrame, window: int) -> pd.Series:
        return df["low"].rolling(window=window, min_periods=window).min()
