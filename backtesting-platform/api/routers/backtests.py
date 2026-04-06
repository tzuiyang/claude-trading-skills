from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api.models.orm import BacktestRun, DailyEquity, Stock, Trade
from api.models.schemas import (
    BacktestCreate,
    BacktestSummary,
    EquityPoint,
    SignalPoint,
    TradeResponse,
)
from api.services.backtest_service import BacktestService

router = APIRouter(prefix="/api/backtests", tags=["backtests"])
backtest_service = BacktestService()


@router.post("", response_model=BacktestSummary)
def create_backtest(body: BacktestCreate, db: Session = Depends(get_db)):
    run = backtest_service.run_backtest(
        db=db,
        ticker=body.ticker,
        strategy_name=body.strategy_name,
        params=body.params,
        start_date=body.start_date,
        end_date=body.end_date,
        initial_capital=body.initial_capital,
    )
    stock = db.query(Stock).get(run.stock_id)
    return _run_to_summary(run, stock.ticker)


@router.get("/compare")
def compare_backtests(run_ids: str, db: Session = Depends(get_db)):
    ids = [int(x.strip()) for x in run_ids.split(",") if x.strip()]
    results = []
    for run_id in ids:
        run = db.query(BacktestRun).get(run_id)
        if not run or run.status != "complete":
            continue
        stock = db.query(Stock).get(run.stock_id)
        equity = (
            db.query(DailyEquity)
            .filter(DailyEquity.backtest_run_id == run_id)
            .order_by(DailyEquity.date)
            .all()
        )
        results.append({
            "run_id": run_id,
            "ticker": stock.ticker,
            "strategy_name": run.strategy_name,
            "total_return_pct": run.total_return_pct,
            "sharpe_ratio": run.sharpe_ratio,
            "max_drawdown_pct": run.max_drawdown_pct,
            "equity_curve": [
                {"date": e.date, "equity": e.equity}
                for e in equity
            ],
        })
    return results


@router.get("/{run_id}", response_model=BacktestSummary)
def get_backtest(run_id: int, db: Session = Depends(get_db)):
    run = db.query(BacktestRun).get(run_id)
    if not run:
        raise HTTPException(404, f"Backtest run {run_id} not found")
    stock = db.query(Stock).get(run.stock_id)
    return _run_to_summary(run, stock.ticker)


@router.get("/{run_id}/trades", response_model=list[TradeResponse])
def get_trades(run_id: int, db: Session = Depends(get_db)):
    trades = (
        db.query(Trade)
        .filter(Trade.backtest_run_id == run_id)
        .order_by(Trade.entry_date)
        .all()
    )
    return [
        TradeResponse(
            id=t.id, entry_date=t.entry_date, exit_date=t.exit_date,
            entry_price=t.entry_price, exit_price=t.exit_price,
            shares=t.shares, direction=t.direction, pnl=t.pnl,
            pnl_pct=t.pnl_pct, mae_pct=t.mae_pct, mfe_pct=t.mfe_pct,
            exit_reason=t.exit_reason,
        )
        for t in trades
    ]


@router.get("/{run_id}/equity", response_model=list[EquityPoint])
def get_equity(run_id: int, db: Session = Depends(get_db)):
    points = (
        db.query(DailyEquity)
        .filter(DailyEquity.backtest_run_id == run_id)
        .order_by(DailyEquity.date)
        .all()
    )
    return [
        EquityPoint(
            date=p.date, equity=p.equity,
            drawdown_pct=p.drawdown_pct, daily_return_pct=p.daily_return_pct,
        )
        for p in points
    ]


@router.get("/{run_id}/signals", response_model=list[SignalPoint])
def get_signals(run_id: int, db: Session = Depends(get_db)):
    trades = (
        db.query(Trade)
        .filter(Trade.backtest_run_id == run_id)
        .order_by(Trade.entry_date)
        .all()
    )
    signals = []
    for t in trades:
        signals.append(SignalPoint(date=t.entry_date, price=t.entry_price, signal="buy"))
        if t.exit_date and t.exit_price:
            signals.append(SignalPoint(date=t.exit_date, price=t.exit_price, signal="sell"))
    return signals


@router.delete("/{run_id}")
def delete_backtest(run_id: int, db: Session = Depends(get_db)):
    run = db.query(BacktestRun).get(run_id)
    if not run:
        raise HTTPException(404, f"Backtest run {run_id} not found")
    db.delete(run)
    db.commit()
    return {"deleted": True}


def _run_to_summary(r: BacktestRun, ticker: str) -> BacktestSummary:
    return BacktestSummary(
        id=r.id, ticker=ticker, strategy_name=r.strategy_name,
        params=r.params, start_date=r.start_date, end_date=r.end_date,
        initial_capital=r.initial_capital, status=r.status,
        total_return_pct=r.total_return_pct, cagr_pct=r.cagr_pct,
        sharpe_ratio=r.sharpe_ratio, sortino_ratio=r.sortino_ratio,
        max_drawdown_pct=r.max_drawdown_pct, win_rate_pct=r.win_rate_pct,
        profit_factor=r.profit_factor, total_trades=r.total_trades,
        avg_trade_duration=r.avg_trade_duration, final_equity=r.final_equity,
        benchmark_return_pct=r.benchmark_return_pct, alpha_pct=r.alpha_pct,
        error_message=r.error_message, created_at=r.created_at,
    )
