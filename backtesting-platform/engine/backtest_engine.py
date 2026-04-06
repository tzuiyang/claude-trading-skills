from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from engine.base_strategy import BaseStrategy
from engine.evaluator import Evaluator
from engine.execution_model import ExecutionModel
from engine.feature_engineer import FeatureEngineer
from engine.result import BacktestResult


@dataclass
class BacktestConfig:
    ticker: str
    strategy: BaseStrategy
    price_df: pd.DataFrame
    start_date: date
    end_date: date
    initial_capital: float = 100_000.0
    commission_pct: float = 0.001
    slippage_pct: float = 0.0005


class BacktestError(Exception):
    pass


class BacktestEngine:
    """Orchestrates the 5-stage pipeline:
    1. Slice data to [start_date, end_date]
    2. FeatureEngineer.compute(required_features)
    3. BaseStrategy.generate_signals(featured_df)
    4. ExecutionModel.simulate(signals, price_df, config)
    5. Evaluator.compute_metrics(equity, trades)
    """

    def __init__(self, config: BacktestConfig) -> None:
        self.config = config
        self._feature_engineer = FeatureEngineer()
        self._execution_model = ExecutionModel(
            commission_pct=config.commission_pct,
            slippage_pct=config.slippage_pct,
        )
        self._evaluator = Evaluator()

    def run(self) -> BacktestResult:
        df = self._slice_data()
        if len(df) < 10:
            raise BacktestError(
                f"Insufficient data: {len(df)} bars for {self.config.ticker} "
                f"between {self.config.start_date} and {self.config.end_date}"
            )

        features = self.config.strategy.required_features()
        df = self._feature_engineer.compute(df, features)

        signals = self.config.strategy.generate_signals(df)

        equity, trades = self._execution_model.simulate(
            signals, df, self.config.initial_capital
        )

        return self._evaluator.compute_metrics(
            equity, trades, self.config.initial_capital
        )

    def _slice_data(self) -> pd.DataFrame:
        df = self.config.price_df.copy()
        start = pd.Timestamp(self.config.start_date)
        end = pd.Timestamp(self.config.end_date)
        return df.loc[start:end]
