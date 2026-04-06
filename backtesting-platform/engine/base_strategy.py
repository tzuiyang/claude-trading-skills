from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class StrategyMetadata:
    name: str
    display_name: str
    description: str
    param_schema: dict
    default_params: dict[str, Any]


class BaseStrategy(ABC):
    """Contract every strategy plugin must satisfy.

    Lifecycle:
        strategy = ConcreteStrategy(params)
        features = strategy.required_features()
        signals  = strategy.generate_signals(df_with_features)
    """

    metadata: StrategyMetadata

    def __init__(self, params: dict[str, Any] | None = None) -> None:
        self.params = {**self.metadata.default_params, **(params or {})}
        self.validate_params(self.params)

    def validate_params(self, params: dict[str, Any]) -> None:
        pass

    @abstractmethod
    def required_features(self) -> list[str]:
        """Return feature column names this strategy needs (e.g. ['sma_20', 'rsi_14'])."""

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Return Series of int: 1=buy, -1=sell, 0=hold. Index must match df.index."""
