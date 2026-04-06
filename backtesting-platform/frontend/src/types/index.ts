export interface Stock {
  id: number;
  ticker: string;
  name: string | null;
  sector: string | null;
  industry: string | null;
  exchange: string | null;
  market_cap: number | null;
}

export interface StockWithMetrics extends Stock {
  latest_backtest_status: string | null;
  total_return_pct: number | null;
  max_drawdown_pct: number | null;
  win_rate_pct: number | null;
  sharpe_ratio: number | null;
  strategies_tested: number;
}

export interface Strategy {
  name: string;
  display_name: string;
  description: string;
  param_schema: Record<string, unknown>;
  default_params: Record<string, unknown>;
}

export interface BacktestSummary {
  id: number;
  ticker: string;
  strategy_name: string;
  params: Record<string, unknown>;
  start_date: string;
  end_date: string;
  initial_capital: number;
  status: string;
  total_return_pct: number | null;
  cagr_pct: number | null;
  sharpe_ratio: number | null;
  sortino_ratio: number | null;
  max_drawdown_pct: number | null;
  win_rate_pct: number | null;
  profit_factor: number | null;
  total_trades: number | null;
  avg_trade_duration: number | null;
  final_equity: number | null;
  error_message: string | null;
  created_at: string;
}

export interface TradeRecord {
  id: number;
  entry_date: string;
  exit_date: string | null;
  entry_price: number;
  exit_price: number | null;
  shares: number;
  direction: string;
  pnl: number | null;
  pnl_pct: number | null;
  exit_reason: string | null;
}

export interface EquityPoint {
  date: string;
  equity: number;
  drawdown_pct: number;
  daily_return_pct: number;
}

export interface SignalPoint {
  date: string;
  price: number;
  signal: "buy" | "sell";
}

export interface PricePoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}
