from __future__ import annotations

from typing import Any

import pandas as pd

from engine.base_strategy import BaseStrategy, StrategyMetadata


class MomentumBreakout(BaseStrategy):
    metadata = StrategyMetadata(
        name="momentum_breakout",
        display_name="Momentum Breakout",
        description=(
            "Buy when price breaks above N-day high with above-average volume; "
            "sell when price drops below trailing stop (ATR-based)."
        ),
        param_schema={
            "type": "object",
            "properties": {
                "breakout_period": {
                    "type": "integer", "minimum": 5, "maximum": 100,
                    "title": "Breakout Lookback (days)",
                },
                "atr_period": {
                    "type": "integer", "minimum": 5, "maximum": 50,
                    "title": "ATR Period",
                },
                "atr_multiplier": {
                    "type": "number", "minimum": 1.0, "maximum": 5.0,
                    "title": "ATR Stop Multiplier",
                },
                "volume_ratio_period": {
                    "type": "integer", "minimum": 5, "maximum": 50,
                    "title": "Volume Avg Period",
                },
                "volume_threshold": {
                    "type": "number", "minimum": 1.0, "maximum": 5.0,
                    "title": "Min Volume Ratio",
                },
            },
            "required": ["breakout_period", "atr_period", "atr_multiplier"],
        },
        default_params={
            "breakout_period": 20,
            "atr_period": 14,
            "atr_multiplier": 2.0,
            "volume_ratio_period": 20,
            "volume_threshold": 1.5,
        },
    )

    def required_features(self) -> list[str]:
        p = self.params
        return [
            f"high_{p['breakout_period']}d",
            f"atr_{p['atr_period']}",
            f"volume_ratio_{p['volume_ratio_period']}",
            f"sma_{p['breakout_period']}",
        ]

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        p = self.params
        high_col = f"high_{p['breakout_period']}d"
        atr_col = f"atr_{p['atr_period']}"
        vol_col = f"volume_ratio_{p['volume_ratio_period']}"
        sma_col = f"sma_{p['breakout_period']}"

        signals = pd.Series(0, index=df.index)

        # Track trailing stop
        in_position = False
        trailing_stop = 0.0

        for i in range(1, len(df)):
            row = df.iloc[i]
            prev_high = df[high_col].iloc[i - 1] if not pd.isna(df[high_col].iloc[i - 1]) else None

            if not in_position:
                # Buy: price breaks above previous N-day high with volume confirmation
                if (
                    prev_high is not None
                    and row["close"] > prev_high
                    and not pd.isna(row[vol_col])
                    and row[vol_col] > p["volume_threshold"]
                    and not pd.isna(row[sma_col])
                    and row["close"] > row[sma_col]
                ):
                    signals.iloc[i] = 1
                    in_position = True
                    trailing_stop = row["close"] - p["atr_multiplier"] * row[atr_col]
            else:
                # Update trailing stop
                if not pd.isna(row[atr_col]):
                    new_stop = row["close"] - p["atr_multiplier"] * row[atr_col]
                    trailing_stop = max(trailing_stop, new_stop)

                # Sell: price drops below trailing stop
                if row["close"] < trailing_stop:
                    signals.iloc[i] = -1
                    in_position = False

        return signals
