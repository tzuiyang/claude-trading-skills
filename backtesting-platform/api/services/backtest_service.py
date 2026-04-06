from __future__ import annotations

import json
import traceback
from datetime import date, datetime

import pandas as pd
from sqlalchemy.orm import Session

from api.models.orm import BacktestRun, DailyEquity, Stock, Trade
from api.services.data_service import DataService
from engine.backtest_engine import BacktestConfig, BacktestEngine
from strategies._registry import STRATEGY_REGISTRY


class BacktestService:
    def __init__(self) -> None:
        self.data_service = DataService()

    def run_backtest(
        self,
        db: Session,
        ticker: str,
        strategy_name: str,
        params: dict,
        start_date: str,
        end_date: str,
        initial_capital: float = 100_000.0,
    ) -> BacktestRun:
        # Get or create stock
        stock = self.data_service.get_or_create_stock(db, ticker)

        # Validate strategy
        if strategy_name not in STRATEGY_REGISTRY:
            raise ValueError(f"Unknown strategy: {strategy_name}. Available: {list(STRATEGY_REGISTRY.keys())}")

        # Create run record
        run = BacktestRun(
            stock_id=stock.id,
            strategy_name=strategy_name,
            params_json=json.dumps(params),
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            status="running",
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        try:
            # Fetch price data (with buffer for indicator warmup)
            warmup_start = pd.Timestamp(start_date) - pd.DateOffset(days=365)
            price_df = self.data_service.get_prices(
                ticker,
                start=str(warmup_start.date()),
                end=end_date,
            )

            # Build and run engine
            strategy_cls = STRATEGY_REGISTRY[strategy_name]
            strategy = strategy_cls(params)

            config = BacktestConfig(
                ticker=ticker,
                strategy=strategy,
                price_df=price_df,
                start_date=date.fromisoformat(start_date),
                end_date=date.fromisoformat(end_date),
                initial_capital=initial_capital,
            )
            engine = BacktestEngine(config)
            result = engine.run()

            # Persist summary metrics
            run.total_return_pct = result.total_return_pct
            run.cagr_pct = result.cagr_pct
            run.sharpe_ratio = result.sharpe_ratio
            run.sortino_ratio = result.sortino_ratio
            run.max_drawdown_pct = result.max_drawdown_pct
            run.win_rate_pct = result.win_rate_pct
            run.profit_factor = result.profit_factor
            run.total_trades = result.total_trades
            run.avg_trade_duration = result.avg_trade_duration_days
            run.final_equity = result.final_equity
            run.benchmark_return_pct = result.benchmark_return_pct
            run.alpha_pct = result.alpha_pct
            run.status = "complete"
            run.completed_at = datetime.utcnow().isoformat()

            # Persist trades
            for t in result.trades:
                trade = Trade(
                    backtest_run_id=run.id,
                    entry_date=t.entry_date,
                    exit_date=t.exit_date,
                    entry_price=t.entry_price,
                    exit_price=t.exit_price,
                    shares=t.shares,
                    direction=t.direction,
                    pnl=t.pnl,
                    pnl_pct=t.pnl_pct,
                    mae_pct=t.mae_pct,
                    mfe_pct=t.mfe_pct,
                    exit_reason=t.exit_reason,
                )
                db.add(trade)

            # Persist daily equity
            for i in range(len(result.equity_series)):
                dt = result.equity_series.index[i]
                date_str = str(dt.date()) if hasattr(dt, "date") else str(dt)[:10]
                eq = DailyEquity(
                    backtest_run_id=run.id,
                    date=date_str,
                    equity=float(result.equity_series.iloc[i]),
                    drawdown_pct=float(result.drawdown_series.iloc[i]),
                    daily_return_pct=float(result.daily_returns.iloc[i]),
                )
                db.add(eq)

            db.commit()

        except Exception as e:
            run.status = "failed"
            run.error_message = f"{type(e).__name__}: {e}\n{traceback.format_exc()[-500:]}"
            run.completed_at = datetime.utcnow().isoformat()
            db.commit()

        db.refresh(run)
        return run
