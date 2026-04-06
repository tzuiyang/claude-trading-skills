from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class TradeRecord:
    entry_date: str
    exit_date: str | None
    entry_price: float
    exit_price: float | None
    shares: float
    direction: str = "long"
    pnl: float | None = None
    pnl_pct: float | None = None
    mae_pct: float | None = None
    mfe_pct: float | None = None
    entry_signal: dict = field(default_factory=dict)
    exit_reason: str = ""


class ExecutionModel:
    """Converts signal Series into equity curve and trade records.

    Rules:
    - Signal 1 on day T → buy at open of T+1 (no look-ahead)
    - Signal -1 on day T → sell at open of T+1
    - One position at a time (no pyramiding)
    - Commission and slippage applied to fill price
    """

    def __init__(
        self,
        commission_pct: float = 0.001,
        slippage_pct: float = 0.0005,
    ) -> None:
        self.commission_pct = commission_pct
        self.slippage_pct = slippage_pct

    def simulate(
        self,
        signals: pd.Series,
        price_df: pd.DataFrame,
        initial_capital: float,
    ) -> tuple[pd.Series, list[TradeRecord]]:
        cash = initial_capital
        shares = 0.0
        trades: list[TradeRecord] = []
        current_trade: dict[str, Any] | None = None

        equity_values = []
        equity_dates = []

        # Shift signals forward: signal on day T executes on T+1 open
        exec_signals = signals.shift(1).fillna(0).astype(int)

        for i in range(len(price_df)):
            row = price_df.iloc[i]
            date_str = str(price_df.index[i].date()) if hasattr(price_df.index[i], "date") else str(price_df.index[i])[:10]
            sig = exec_signals.iloc[i]

            # Execute buy
            if sig == 1 and shares == 0:
                fill_price = row["open"] * (1 + self.slippage_pct)
                commission = fill_price * self.commission_pct
                cost_per_share = fill_price + commission
                shares = int(cash / cost_per_share)
                if shares > 0:
                    cash -= shares * cost_per_share
                    current_trade = {
                        "entry_date": date_str,
                        "entry_price": fill_price,
                        "shares": shares,
                        "min_price": row["low"],
                        "max_price": row["high"],
                    }

            # Execute sell
            elif sig == -1 and shares > 0 and current_trade is not None:
                fill_price = row["open"] * (1 - self.slippage_pct)
                commission = fill_price * self.commission_pct
                proceeds_per_share = fill_price - commission
                cash += shares * proceeds_per_share

                entry_price = current_trade["entry_price"]
                pnl = (proceeds_per_share - entry_price) * shares
                pnl_pct = (proceeds_per_share / entry_price - 1) * 100
                mae_pct = (current_trade["min_price"] / entry_price - 1) * 100
                mfe_pct = (current_trade["max_price"] / entry_price - 1) * 100

                trades.append(TradeRecord(
                    entry_date=current_trade["entry_date"],
                    exit_date=date_str,
                    entry_price=entry_price,
                    exit_price=fill_price,
                    shares=shares,
                    pnl=round(pnl, 2),
                    pnl_pct=round(pnl_pct, 4),
                    mae_pct=round(mae_pct, 4),
                    mfe_pct=round(mfe_pct, 4),
                    exit_reason="signal",
                ))
                shares = 0.0
                current_trade = None

            # Track MAE/MFE during holding
            if current_trade is not None and shares > 0:
                current_trade["min_price"] = min(current_trade["min_price"], row["low"])
                current_trade["max_price"] = max(current_trade["max_price"], row["high"])

            # Record equity
            mark_to_market = cash + shares * row["close"]
            equity_values.append(mark_to_market)
            equity_dates.append(price_df.index[i])

        # Close open position at end
        if shares > 0 and current_trade is not None:
            last_row = price_df.iloc[-1]
            last_date = str(price_df.index[-1].date()) if hasattr(price_df.index[-1], "date") else str(price_df.index[-1])[:10]
            fill_price = last_row["close"]
            entry_price = current_trade["entry_price"]
            pnl = (fill_price - entry_price) * shares
            pnl_pct = (fill_price / entry_price - 1) * 100

            trades.append(TradeRecord(
                entry_date=current_trade["entry_date"],
                exit_date=last_date,
                entry_price=entry_price,
                exit_price=fill_price,
                shares=shares,
                pnl=round(pnl, 2),
                pnl_pct=round(pnl_pct, 4),
                mae_pct=round((current_trade["min_price"] / entry_price - 1) * 100, 4),
                mfe_pct=round((current_trade["max_price"] / entry_price - 1) * 100, 4),
                exit_reason="end_of_period",
            ))

        equity = pd.Series(equity_values, index=equity_dates, name="equity")
        return equity, trades
