from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd

from engine.execution_model import TradeRecord
from engine.result import BacktestResult


class Evaluator:
    """Computes all performance metrics from equity series and trade list."""

    TRADING_DAYS_PER_YEAR = 252

    def compute_metrics(
        self,
        equity: pd.Series,
        trades: list[TradeRecord],
        initial_capital: float,
        benchmark_return_pct: float | None = None,
    ) -> BacktestResult:
        daily_returns = equity.pct_change().fillna(0)
        drawdown = self._drawdown_series(equity)
        dd_min_idx = drawdown.idxmin()

        # Find peak before trough
        peak_date = equity.loc[:dd_min_idx].idxmax()

        total_return = (equity.iloc[-1] / initial_capital - 1) * 100
        n_days = len(equity)
        years = n_days / self.TRADING_DAYS_PER_YEAR

        alpha = None
        if benchmark_return_pct is not None:
            alpha = round(total_return - benchmark_return_pct, 4)

        avg_duration = 0.0
        if trades:
            durations = []
            for t in trades:
                if t.exit_date and t.entry_date:
                    d1 = datetime.strptime(t.entry_date, "%Y-%m-%d")
                    d2 = datetime.strptime(t.exit_date, "%Y-%m-%d")
                    durations.append((d2 - d1).days)
            avg_duration = np.mean(durations) if durations else 0.0

        return BacktestResult(
            total_return_pct=round(total_return, 4),
            cagr_pct=round(self._cagr(equity, initial_capital, years), 4),
            sharpe_ratio=round(self._sharpe(daily_returns), 4),
            sortino_ratio=round(self._sortino(daily_returns), 4),
            max_drawdown_pct=round(drawdown.min() * 100, 4),
            max_drawdown_peak_date=str(peak_date)[:10],
            max_drawdown_trough_date=str(dd_min_idx)[:10],
            win_rate_pct=round(self._win_rate(trades), 4),
            profit_factor=round(self._profit_factor(trades), 4),
            total_trades=len(trades),
            avg_trade_duration_days=round(avg_duration, 1),
            final_equity=round(equity.iloc[-1], 2),
            benchmark_return_pct=benchmark_return_pct,
            alpha_pct=alpha,
            equity_series=equity,
            drawdown_series=drawdown * 100,
            daily_returns=daily_returns * 100,
            trades=trades,
        )

    @staticmethod
    def _cagr(equity: pd.Series, initial_capital: float, years: float) -> float:
        if years <= 0 or initial_capital <= 0:
            return 0.0
        return ((equity.iloc[-1] / initial_capital) ** (1 / years) - 1) * 100

    @staticmethod
    def _sharpe(daily_returns: pd.Series, risk_free_rate: float = 0.05) -> float:
        if len(daily_returns) < 2:
            return 0.0
        excess = daily_returns - risk_free_rate / 252
        std = excess.std()
        if std == 0 or np.isnan(std) or std < 1e-10:
            return 0.0
        return float(np.sqrt(252) * excess.mean() / std)

    @staticmethod
    def _sortino(daily_returns: pd.Series, risk_free_rate: float = 0.05) -> float:
        if len(daily_returns) < 2:
            return 0.0
        excess = daily_returns - risk_free_rate / 252
        downside = excess[excess < 0]
        if len(downside) == 0 or np.isnan(downside.std()) or downside.std() < 1e-10:
            return 0.0
        return float(np.sqrt(252) * excess.mean() / downside.std())

    @staticmethod
    def _drawdown_series(equity: pd.Series) -> pd.Series:
        peak = equity.cummax()
        return (equity - peak) / peak

    @staticmethod
    def _win_rate(trades: list[TradeRecord]) -> float:
        if not trades:
            return 0.0
        winners = sum(1 for t in trades if t.pnl is not None and t.pnl > 0)
        return (winners / len(trades)) * 100

    @staticmethod
    def _profit_factor(trades: list[TradeRecord]) -> float:
        gross_profit = sum(t.pnl for t in trades if t.pnl is not None and t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in trades if t.pnl is not None and t.pnl < 0))
        if gross_loss == 0:
            return float("inf") if gross_profit > 0 else 0.0
        return gross_profit / gross_loss
