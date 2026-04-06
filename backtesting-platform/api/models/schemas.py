from __future__ import annotations

from pydantic import BaseModel


class StockCreate(BaseModel):
    ticker: str


class StockResponse(BaseModel):
    id: int
    ticker: str
    name: str | None = None
    sector: str | None = None
    industry: str | None = None
    exchange: str | None = None
    market_cap: float | None = None


class StockWithMetrics(StockResponse):
    latest_backtest_status: str | None = None
    total_return_pct: float | None = None
    max_drawdown_pct: float | None = None
    win_rate_pct: float | None = None
    sharpe_ratio: float | None = None
    strategies_tested: int = 0


class UniverseCreate(BaseModel):
    name: str
    description: str | None = None
    tickers: list[str] = []


class UniverseResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    stock_count: int = 0


class UniverseDetailResponse(UniverseResponse):
    stocks: list[StockWithMetrics] = []


class StrategyInfo(BaseModel):
    name: str
    display_name: str
    description: str
    param_schema: dict
    default_params: dict


class BacktestCreate(BaseModel):
    ticker: str
    strategy_name: str
    params: dict = {}
    start_date: str
    end_date: str
    initial_capital: float = 100_000.0


class BacktestSummary(BaseModel):
    id: int
    ticker: str
    strategy_name: str
    params: dict
    start_date: str
    end_date: str
    initial_capital: float
    status: str
    total_return_pct: float | None = None
    cagr_pct: float | None = None
    sharpe_ratio: float | None = None
    sortino_ratio: float | None = None
    max_drawdown_pct: float | None = None
    win_rate_pct: float | None = None
    profit_factor: float | None = None
    total_trades: int | None = None
    avg_trade_duration: float | None = None
    final_equity: float | None = None
    benchmark_return_pct: float | None = None
    alpha_pct: float | None = None
    error_message: str | None = None
    created_at: str


class TradeResponse(BaseModel):
    id: int
    entry_date: str
    exit_date: str | None = None
    entry_price: float
    exit_price: float | None = None
    shares: float
    direction: str
    pnl: float | None = None
    pnl_pct: float | None = None
    mae_pct: float | None = None
    mfe_pct: float | None = None
    exit_reason: str | None = None


class EquityPoint(BaseModel):
    date: str
    equity: float
    drawdown_pct: float
    daily_return_pct: float


class SignalPoint(BaseModel):
    date: str
    price: float
    signal: str  # "buy" or "sell"
