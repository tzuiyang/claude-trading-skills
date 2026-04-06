import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { getStockBacktests, getStockPrices } from "../api/stocks";
import { listStrategies } from "../api/strategies";
import { runBacktest, getEquityCurve, getSignals, getTrades } from "../api/backtests";
import EquityChart from "../components/charts/EquityChart";
import DrawdownChart from "../components/charts/DrawdownChart";
import PriceSignalChart from "../components/charts/PriceSignalChart";
import type {
  BacktestSummary,
  Strategy,
  EquityPoint,
  SignalPoint,
  PricePoint,
  TradeRecord,
} from "../types";

function fmt(v: number | null | undefined, d = 2) {
  return v != null ? v.toFixed(d) : "—";
}

function MetricCard({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="metric-card">
      <div className="metric-label">{label}</div>
      <div className="metric-value" style={{ color }}>{value}</div>
    </div>
  );
}

export default function StockDetailPage() {
  const { ticker } = useParams<{ ticker: string }>();
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState("");
  const [params, setParams] = useState<Record<string, unknown>>({});
  const [startDate, setStartDate] = useState("2023-01-01");
  const [endDate, setEndDate] = useState("2025-12-31");
  const [running, setRunning] = useState(false);

  const [backtests, setBacktests] = useState<BacktestSummary[]>([]);
  const [selectedRun, setSelectedRun] = useState<BacktestSummary | null>(null);
  const [equityData, setEquityData] = useState<EquityPoint[]>([]);
  const [signals, setSignals] = useState<SignalPoint[]>([]);
  const [prices, setPrices] = useState<PricePoint[]>([]);
  const [trades, setTrades] = useState<TradeRecord[]>([]);
  const [sliceEnd, setSliceEnd] = useState<number | undefined>(undefined);

  useEffect(() => {
    listStrategies().then(s => {
      setStrategies(s);
      if (s.length > 0) {
        setSelectedStrategy(s[0].name);
        setParams({ ...s[0].default_params });
      }
    });
    if (ticker) {
      getStockBacktests(ticker).then(setBacktests);
    }
  }, [ticker]);

  const currentStrategy = strategies.find(s => s.name === selectedStrategy);

  const handleStrategyChange = (name: string) => {
    setSelectedStrategy(name);
    const s = strategies.find(st => st.name === name);
    if (s) setParams({ ...s.default_params });
  };

  const handleRun = async () => {
    if (!ticker || !selectedStrategy) return;
    setRunning(true);
    try {
      const result = await runBacktest({
        ticker,
        strategy_name: selectedStrategy,
        params,
        start_date: startDate,
        end_date: endDate,
      });
      setBacktests(prev => [result, ...prev]);
      if (result.status === "complete") {
        await loadRunData(result);
      }
    } finally {
      setRunning(false);
    }
  };

  const loadRunData = async (run: BacktestSummary) => {
    setSelectedRun(run);
    const [eq, sig, tr, pr] = await Promise.all([
      getEquityCurve(run.id),
      getSignals(run.id),
      getTrades(run.id),
      ticker ? getStockPrices(ticker, run.start_date, run.end_date) : Promise.resolve([]),
    ]);
    setEquityData(eq);
    setSignals(sig);
    setTrades(tr);
    setPrices(pr);
    setSliceEnd(undefined);
  };

  const paramProperties = currentStrategy?.param_schema
    ? (currentStrategy.param_schema as { properties?: Record<string, { title?: string; type?: string }> }).properties || {}
    : {};

  return (
    <div>
      <div className="flex-row gap-8 mb-16">
        <Link to="/" style={{ color: "var(--text-muted)", textDecoration: "none", fontSize: 14 }}>
          ← Universe
        </Link>
        <h1 className="page-title" style={{ margin: 0 }}>{ticker}</h1>
      </div>

      {/* Strategy Controls */}
      <div className="card">
        <div className="section-title">Run Backtest</div>
        <div className="flex-row gap-8 mb-16" style={{ flexWrap: "wrap" }}>
          <select
            className="input"
            value={selectedStrategy}
            onChange={e => handleStrategyChange(e.target.value)}
          >
            {strategies.map(s => (
              <option key={s.name} value={s.name}>{s.display_name}</option>
            ))}
          </select>
          <input
            className="input"
            type="date"
            value={startDate}
            onChange={e => setStartDate(e.target.value)}
          />
          <input
            className="input"
            type="date"
            value={endDate}
            onChange={e => setEndDate(e.target.value)}
          />
          <button className="btn btn-primary" onClick={handleRun} disabled={running}>
            {running ? <><span className="spinner" /> Running...</> : "Run Backtest"}
          </button>
        </div>

        {/* Strategy parameters */}
        {Object.keys(paramProperties).length > 0 && (
          <div className="flex-row gap-8" style={{ flexWrap: "wrap" }}>
            {Object.entries(paramProperties).map(([key, schema]) => (
              <label key={key} style={{ fontSize: 12, color: "var(--text-secondary)" }}>
                {schema.title || key}
                <input
                  className="input"
                  type="number"
                  value={String(params[key] ?? "")}
                  onChange={e => {
                    const v = schema.type === "integer" ? parseInt(e.target.value) : parseFloat(e.target.value);
                    setParams(prev => ({ ...prev, [key]: isNaN(v) ? e.target.value : v }));
                  }}
                  style={{ display: "block", marginTop: 4, width: 120 }}
                />
              </label>
            ))}
          </div>
        )}

        {currentStrategy && (
          <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 8 }}>
            {currentStrategy.description}
          </p>
        )}
      </div>

      {/* Metrics */}
      {selectedRun && selectedRun.status === "complete" && (
        <>
          <div className="metrics-row">
            <MetricCard
              label="Total Return"
              value={`${fmt(selectedRun.total_return_pct)}%`}
              color={selectedRun.total_return_pct != null && selectedRun.total_return_pct >= 0 ? "var(--green)" : "var(--red)"}
            />
            <MetricCard label="CAGR" value={`${fmt(selectedRun.cagr_pct)}%`} />
            <MetricCard
              label="Sharpe"
              value={fmt(selectedRun.sharpe_ratio)}
              color={selectedRun.sharpe_ratio != null && selectedRun.sharpe_ratio >= 1 ? "var(--green)" : undefined}
            />
            <MetricCard label="Max Drawdown" value={`${fmt(selectedRun.max_drawdown_pct)}%`} color="var(--red)" />
            <MetricCard label="Win Rate" value={`${fmt(selectedRun.win_rate_pct)}%`} />
            <MetricCard label="Profit Factor" value={fmt(selectedRun.profit_factor)} />
            <MetricCard label="Trades" value={String(selectedRun.total_trades ?? 0)} />
          </div>

          {/* Time Slider */}
          {equityData.length > 0 && (
            <div className="card">
              <div className="flex-between mb-8">
                <span className="section-title" style={{ margin: 0 }}>Timeline</span>
                <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                  {sliceEnd != null ? equityData[sliceEnd]?.date : equityData[equityData.length - 1]?.date}
                </span>
              </div>
              <input
                type="range"
                min={0}
                max={equityData.length - 1}
                value={sliceEnd ?? equityData.length - 1}
                onChange={e => setSliceEnd(parseInt(e.target.value))}
                style={{ width: "100%", accentColor: "var(--accent)" }}
              />
            </div>
          )}

          {/* Charts */}
          <div className="card">
            <div className="section-title">Equity Curve</div>
            <EquityChart data={equityData} sliceEnd={sliceEnd} />
          </div>

          <div className="card">
            <div className="section-title">Drawdown</div>
            <DrawdownChart data={equityData} sliceEnd={sliceEnd} />
          </div>

          {prices.length > 0 && (
            <div className="card">
              <div className="section-title">Price + Buy/Sell Signals</div>
              <PriceSignalChart prices={prices} signals={signals} sliceEnd={sliceEnd} />
            </div>
          )}

          {/* Trades Table */}
          {trades.length > 0 && (
            <div className="card" style={{ padding: 0, overflow: "auto" }}>
              <div className="section-title" style={{ padding: "16px 16px 0" }}>Trades ({trades.length})</div>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Entry</th>
                    <th>Exit</th>
                    <th>Entry $</th>
                    <th>Exit $</th>
                    <th>Shares</th>
                    <th>P&L</th>
                    <th>P&L %</th>
                    <th>Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {trades.map(t => (
                    <tr key={t.id}>
                      <td>{t.entry_date}</td>
                      <td>{t.exit_date || "—"}</td>
                      <td>${t.entry_price.toFixed(2)}</td>
                      <td>{t.exit_price != null ? `$${t.exit_price.toFixed(2)}` : "—"}</td>
                      <td>{t.shares}</td>
                      <td className={t.pnl != null ? (t.pnl >= 0 ? "positive" : "negative") : ""}>
                        {t.pnl != null ? `$${t.pnl.toLocaleString()}` : "—"}
                      </td>
                      <td className={t.pnl_pct != null ? (t.pnl_pct >= 0 ? "positive" : "negative") : ""}>
                        {fmt(t.pnl_pct)}%
                      </td>
                      <td style={{ color: "var(--text-muted)" }}>{t.exit_reason || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {selectedRun && selectedRun.status === "failed" && (
        <div className="card" style={{ borderColor: "var(--red)" }}>
          <div className="section-title" style={{ color: "var(--red)" }}>Backtest Failed</div>
          <pre style={{ fontSize: 12, color: "var(--text-muted)", whiteSpace: "pre-wrap" }}>
            {selectedRun.error_message}
          </pre>
        </div>
      )}

      {/* History */}
      {backtests.length > 0 && (
        <div className="card" style={{ padding: 0, overflow: "auto" }}>
          <div className="section-title" style={{ padding: "16px 16px 0" }}>Backtest History</div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Strategy</th>
                <th>Period</th>
                <th>Status</th>
                <th>Return %</th>
                <th>Sharpe</th>
                <th>Max DD %</th>
                <th>Trades</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {backtests.map(b => (
                <tr key={b.id}>
                  <td style={{ fontWeight: 500 }}>{b.strategy_name}</td>
                  <td style={{ color: "var(--text-muted)" }}>{b.start_date} → {b.end_date}</td>
                  <td>
                    <span className={`badge badge-${b.status}`}>{b.status}</span>
                  </td>
                  <td className={b.total_return_pct != null ? (b.total_return_pct >= 0 ? "positive" : "negative") : ""}>
                    {fmt(b.total_return_pct)}
                  </td>
                  <td>{fmt(b.sharpe_ratio)}</td>
                  <td className="negative">{fmt(b.max_drawdown_pct)}</td>
                  <td>{b.total_trades ?? "—"}</td>
                  <td>
                    {b.status === "complete" && (
                      <button className="btn" onClick={() => loadRunData(b)} style={{ padding: "4px 10px" }}>
                        View
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
