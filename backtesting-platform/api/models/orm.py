from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base


class Universe(Base):
    __tablename__ = "universes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String, default=lambda: datetime.utcnow().isoformat())

    stocks: Mapped[list[UniverseStock]] = relationship(back_populates="universe", cascade="all, delete-orphan")


class Stock(Base):
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String)
    sector: Mapped[str | None] = mapped_column(String)
    industry: Mapped[str | None] = mapped_column(String)
    exchange: Mapped[str | None] = mapped_column(String)
    market_cap: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[str] = mapped_column(String, default=lambda: datetime.utcnow().isoformat())

    universe_links: Mapped[list[UniverseStock]] = relationship(back_populates="stock")
    backtest_runs: Mapped[list[BacktestRun]] = relationship(back_populates="stock")


class UniverseStock(Base):
    __tablename__ = "universe_stocks"

    universe_id: Mapped[int] = mapped_column(ForeignKey("universes.id", ondelete="CASCADE"), primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), primary_key=True)
    added_at: Mapped[str] = mapped_column(String, default=lambda: datetime.utcnow().isoformat())

    universe: Mapped[Universe] = relationship(back_populates="stocks")
    stock: Mapped[Stock] = relationship(back_populates="universe_links")


class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), nullable=False, index=True)
    strategy_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    params_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    start_date: Mapped[str] = mapped_column(String, nullable=False)
    end_date: Mapped[str] = mapped_column(String, nullable=False)
    initial_capital: Mapped[float] = mapped_column(Float, default=100_000.0)

    # Summary metrics
    total_return_pct: Mapped[float | None] = mapped_column(Float)
    cagr_pct: Mapped[float | None] = mapped_column(Float)
    sharpe_ratio: Mapped[float | None] = mapped_column(Float)
    sortino_ratio: Mapped[float | None] = mapped_column(Float)
    max_drawdown_pct: Mapped[float | None] = mapped_column(Float)
    win_rate_pct: Mapped[float | None] = mapped_column(Float)
    profit_factor: Mapped[float | None] = mapped_column(Float)
    total_trades: Mapped[int | None] = mapped_column(Integer)
    avg_trade_duration: Mapped[float | None] = mapped_column(Float)
    final_equity: Mapped[float | None] = mapped_column(Float)
    benchmark_return_pct: Mapped[float | None] = mapped_column(Float)
    alpha_pct: Mapped[float | None] = mapped_column(Float)

    status: Mapped[str] = mapped_column(String, default="pending", index=True)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String, default=lambda: datetime.utcnow().isoformat())
    completed_at: Mapped[str | None] = mapped_column(String)

    stock: Mapped[Stock] = relationship(back_populates="backtest_runs")
    trades: Mapped[list[Trade]] = relationship(back_populates="backtest_run", cascade="all, delete-orphan")
    daily_equity: Mapped[list[DailyEquity]] = relationship(back_populates="backtest_run", cascade="all, delete-orphan")

    @property
    def params(self) -> dict:
        return json.loads(self.params_json)


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    backtest_run_id: Mapped[int] = mapped_column(ForeignKey("backtest_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    entry_date: Mapped[str] = mapped_column(String, nullable=False)
    exit_date: Mapped[str | None] = mapped_column(String)
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    exit_price: Mapped[float | None] = mapped_column(Float)
    shares: Mapped[float] = mapped_column(Float, nullable=False)
    direction: Mapped[str] = mapped_column(String, default="long")
    pnl: Mapped[float | None] = mapped_column(Float)
    pnl_pct: Mapped[float | None] = mapped_column(Float)
    mae_pct: Mapped[float | None] = mapped_column(Float)
    mfe_pct: Mapped[float | None] = mapped_column(Float)
    exit_reason: Mapped[str | None] = mapped_column(String)

    backtest_run: Mapped[BacktestRun] = relationship(back_populates="trades")


class DailyEquity(Base):
    __tablename__ = "daily_equity"
    __table_args__ = (
        UniqueConstraint("backtest_run_id", "date"),
        Index("idx_equity_run_date", "backtest_run_id", "date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    backtest_run_id: Mapped[int] = mapped_column(ForeignKey("backtest_runs.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[str] = mapped_column(String, nullable=False)
    equity: Mapped[float] = mapped_column(Float, nullable=False)
    drawdown_pct: Mapped[float] = mapped_column(Float, nullable=False)
    daily_return_pct: Mapped[float] = mapped_column(Float, nullable=False)
    cash: Mapped[float] = mapped_column(Float, default=0.0)

    backtest_run: Mapped[BacktestRun] = relationship(back_populates="daily_equity")
