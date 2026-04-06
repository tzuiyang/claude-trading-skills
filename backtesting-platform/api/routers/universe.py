from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api.models.orm import BacktestRun, Stock, Universe, UniverseStock
from api.models.schemas import (
    StockWithMetrics,
    UniverseCreate,
    UniverseDetailResponse,
    UniverseResponse,
)
from api.services.data_service import DataService

router = APIRouter(prefix="/api/universe", tags=["universe"])
data_service = DataService()


@router.get("", response_model=list[UniverseResponse])
def list_universes(db: Session = Depends(get_db)):
    universes = db.query(Universe).order_by(Universe.name).all()
    return [
        UniverseResponse(
            id=u.id, name=u.name, description=u.description,
            stock_count=len(u.stocks),
        )
        for u in universes
    ]


@router.post("", response_model=UniverseDetailResponse)
def create_universe(body: UniverseCreate, db: Session = Depends(get_db)):
    universe = Universe(name=body.name, description=body.description)
    db.add(universe)
    db.commit()
    db.refresh(universe)

    stocks_with_metrics = []
    for ticker in body.tickers:
        stock = data_service.get_or_create_stock(db, ticker)
        link = UniverseStock(universe_id=universe.id, stock_id=stock.id)
        db.add(link)
        stocks_with_metrics.append(StockWithMetrics(
            id=stock.id, ticker=stock.ticker, name=stock.name,
            sector=stock.sector, industry=stock.industry,
            exchange=stock.exchange, market_cap=stock.market_cap,
        ))
    db.commit()

    return UniverseDetailResponse(
        id=universe.id, name=universe.name, description=universe.description,
        stock_count=len(stocks_with_metrics), stocks=stocks_with_metrics,
    )


@router.get("/{universe_id}/stocks", response_model=list[StockWithMetrics])
def get_universe_stocks(universe_id: int, db: Session = Depends(get_db)):
    universe = db.query(Universe).get(universe_id)
    if not universe:
        raise HTTPException(404, f"Universe {universe_id} not found")

    result = []
    for link in universe.stocks:
        s = link.stock
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
            id=s.id, ticker=s.ticker, name=s.name,
            sector=s.sector, industry=s.industry,
            exchange=s.exchange, market_cap=s.market_cap,
            latest_backtest_status=latest.status if latest else None,
            total_return_pct=latest.total_return_pct if latest else None,
            max_drawdown_pct=latest.max_drawdown_pct if latest else None,
            win_rate_pct=latest.win_rate_pct if latest else None,
            sharpe_ratio=latest.sharpe_ratio if latest else None,
            strategies_tested=strategies_tested,
        ))
    return result


@router.post("/{universe_id}/stocks")
def add_stocks_to_universe(universe_id: int, tickers: list[str], db: Session = Depends(get_db)):
    universe = db.query(Universe).get(universe_id)
    if not universe:
        raise HTTPException(404, f"Universe {universe_id} not found")

    added = []
    for ticker in tickers:
        stock = data_service.get_or_create_stock(db, ticker)
        existing = db.query(UniverseStock).filter_by(
            universe_id=universe_id, stock_id=stock.id
        ).first()
        if not existing:
            link = UniverseStock(universe_id=universe_id, stock_id=stock.id)
            db.add(link)
            added.append(ticker.upper())
    db.commit()
    return {"added": added}
