from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api.models.orm import BacktestRun, Stock
from api.models.schemas import BacktestSummary, StockCreate, StockResponse, StockWithMetrics
from api.services.data_service import DataService

router = APIRouter(prefix="/api/stocks", tags=["stocks"])
data_service = DataService()


@router.get("", response_model=list[StockWithMetrics])
def list_stocks(db: Session = Depends(get_db)):
    stocks = db.query(Stock).order_by(Stock.ticker).all()
    result = []
    for s in stocks:
        latest = (
            db.query(BacktestRun)
            .filter(BacktestRun.stock_id == s.id, BacktestRun.status == "complete")
            .order_by(BacktestRun.created_at.desc())
            .first()
        )
        strategies_tested = (
            db.query(BacktestRun.strategy_name)
            .filter(BacktestRun.stock_id == s.id, BacktestRun.status == "complete")
            .distinct()
            .count()
        )
        result.append(StockWithMetrics(
            id=s.id,
            ticker=s.ticker,
            name=s.name,
            sector=s.sector,
            industry=s.industry,
            exchange=s.exchange,
            market_cap=s.market_cap,
            latest_backtest_status=latest.status if latest else None,
            total_return_pct=latest.total_return_pct if latest else None,
            max_drawdown_pct=latest.max_drawdown_pct if latest else None,
            win_rate_pct=latest.win_rate_pct if latest else None,
            sharpe_ratio=latest.sharpe_ratio if latest else None,
            strategies_tested=strategies_tested,
        ))
    return result


@router.post("", response_model=StockResponse)
def create_stock(body: StockCreate, db: Session = Depends(get_db)):
    stock = data_service.get_or_create_stock(db, body.ticker)
    return StockResponse(
        id=stock.id, ticker=stock.ticker, name=stock.name,
        sector=stock.sector, industry=stock.industry,
        exchange=stock.exchange, market_cap=stock.market_cap,
    )


@router.get("/{ticker}", response_model=StockResponse)
def get_stock(ticker: str, db: Session = Depends(get_db)):
    stock = db.query(Stock).filter(Stock.ticker == ticker.upper()).first()
    if not stock:
        raise HTTPException(404, f"Stock {ticker} not found")
    return StockResponse(
        id=stock.id, ticker=stock.ticker, name=stock.name,
        sector=stock.sector, industry=stock.industry,
        exchange=stock.exchange, market_cap=stock.market_cap,
    )


@router.get("/{ticker}/backtests", response_model=list[BacktestSummary])
def get_stock_backtests(ticker: str, db: Session = Depends(get_db)):
    stock = db.query(Stock).filter(Stock.ticker == ticker.upper()).first()
    if not stock:
        raise HTTPException(404, f"Stock {ticker} not found")
    runs = (
        db.query(BacktestRun)
        .filter(BacktestRun.stock_id == stock.id)
        .order_by(BacktestRun.created_at.desc())
        .all()
    )
    return [_run_to_summary(r, stock.ticker) for r in runs]


@router.get("/{ticker}/prices")
def get_stock_prices(ticker: str, start: str | None = None, end: str | None = None):
    try:
        df = data_service.get_prices(ticker.upper(), start=start, end=end)
    except ValueError as e:
        raise HTTPException(404, str(e))
    records = []
    for dt, row in df.iterrows():
        date_str = str(dt.date()) if hasattr(dt, "date") else str(dt)[:10]
        records.append({
            "date": date_str,
            "open": round(row["open"], 2),
            "high": round(row["high"], 2),
            "low": round(row["low"], 2),
            "close": round(row["close"], 2),
            "volume": int(row["volume"]),
        })
    return records


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
