from __future__ import annotations

from typing import Any

import pandas as pd

from engine.base_strategy import BaseStrategy, StrategyMetadata


class RSIMeanReversion(BaseStrategy):
    metadata = StrategyMetadata(
        name="rsi_mean_reversion",
        display_name="RSI Mean Reversion",
        description="Buy when RSI drops below oversold level; sell when it rises above overbought.",
        param_schema={
            "type": "object",
            "properties": {
                "rsi_period": {
                    "type": "integer", "minimum": 2, "maximum": 50,
                    "title": "RSI Period",
                },
                "oversold": {
                    "type": "number", "minimum": 10, "maximum": 50,
                    "title": "Oversold Threshold",
                },
                "overbought": {
                    "type": "number", "minimum": 50, "maximum": 90,
                    "title": "Overbought Threshold",
                },
            },
            "required": ["rsi_period", "oversold", "overbought"],
        },
        default_params={"rsi_period": 14, "oversold": 30, "overbought": 70},
    )

    def validate_params(self, params: dict[str, Any]) -> None:
        if params["oversold"] >= params["overbought"]:
            raise ValueError("oversold must be less than overbought")

    def required_features(self) -> list[str]:
        return [f"rsi_{self.params['rsi_period']}"]

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        rsi_col = f"rsi_{self.params['rsi_period']}"
        rsi = df[rsi_col]
        signals = pd.Series(0, index=df.index)
        signals[rsi < self.params["oversold"]] = 1
        signals[rsi > self.params["overbought"]] = -1
        return signals
