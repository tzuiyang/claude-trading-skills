from __future__ import annotations

from typing import Any

import pandas as pd

from engine.base_strategy import BaseStrategy, StrategyMetadata


class MovingAverageCrossover(BaseStrategy):
    metadata = StrategyMetadata(
        name="moving_average_crossover",
        display_name="Moving Average Crossover",
        description="Buy when fast SMA crosses above slow SMA; sell on cross below.",
        param_schema={
            "type": "object",
            "properties": {
                "fast_period": {
                    "type": "integer", "minimum": 2, "maximum": 100,
                    "title": "Fast SMA Period",
                },
                "slow_period": {
                    "type": "integer", "minimum": 10, "maximum": 300,
                    "title": "Slow SMA Period",
                },
            },
            "required": ["fast_period", "slow_period"],
        },
        default_params={"fast_period": 20, "slow_period": 50},
    )

    def validate_params(self, params: dict[str, Any]) -> None:
        if params["fast_period"] >= params["slow_period"]:
            raise ValueError("fast_period must be less than slow_period")

    def required_features(self) -> list[str]:
        return [f"sma_{self.params['fast_period']}", f"sma_{self.params['slow_period']}"]

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        fast_col = f"sma_{self.params['fast_period']}"
        slow_col = f"sma_{self.params['slow_period']}"
        fast_above = df[fast_col] > df[slow_col]
        signals = pd.Series(0, index=df.index)
        signals[fast_above & ~fast_above.shift(1).fillna(False)] = 1
        signals[~fast_above & fast_above.shift(1).fillna(True)] = -1
        return signals
