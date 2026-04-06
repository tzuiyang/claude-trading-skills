from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from engine.execution_model import TradeRecord


@dataclass
class BacktestResult:
    total_return_pct: float
    cagr_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float
    max_drawdown_peak_date: str
    max_drawdown_trough_date: str
    win_rate_pct: float
    profit_factor: float
    total_trades: int
    avg_trade_duration_days: float
    final_equity: float
    benchmark_return_pct: float | None = None
    alpha_pct: float | None = None

    equity_series: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))
    drawdown_series: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))
    daily_returns: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))

    trades: list[TradeRecord] = field(default_factory=list)

    def to_summary_dict(self) -> dict:
        return {
            "total_return_pct": self.total_return_pct,
            "cagr_pct": self.cagr_pct,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "max_drawdown_pct": self.max_drawdown_pct,
            "win_rate_pct": self.win_rate_pct,
            "profit_factor": self.profit_factor,
            "total_trades": self.total_trades,
            "avg_trade_duration_days": self.avg_trade_duration_days,
            "final_equity": self.final_equity,
            "benchmark_return_pct": self.benchmark_return_pct,
            "alpha_pct": self.alpha_pct,
        }
