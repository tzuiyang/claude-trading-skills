import { useState } from "react";
import { compareBacktests } from "../api/backtests";
import { listStocks, getStockBacktests } from "../api/stocks";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from "recharts";

const COLORS = ["#38bdf8", "#22c55e", "#eab308", "#ef4444", "#a855f7", "#f97316"];

interface CompareResult {
  run_id: number;
  ticker: string;
  strategy_name: string;
  total_return_pct: number;
  sharpe_ratio: number;
  max_drawdown_pct: number;
  equity_curve: { date: string; equity: number }[];
}

function fmt(v: number | null, d = 2) {
  return v != null ? v.toFixed(d) : "—";
}

export default function ComparisonPage() {
  const [results, setResults] = useState<CompareResult[]>([]);
  const [loading, setLoading] = useState(false);

  const loadComparison = async () => {
    const allStocks = await listStocks();

    const runIds: number[] = [];
    for (const s of allStocks) {
      if (s.strategies_tested > 0) {
        const backtests = await getStockBacktests(s.ticker);
        for (const b of backtests) {
          if (b.status === "complete") runIds.push(b.id);
        }
      }
    }

    if (runIds.length === 0) {
      setResults([]);
      return;
    }

    setLoading(true);
    try {
      const res = await compareBacktests(runIds.slice(0, 10));
      setResults(res);
    } finally {
      setLoading(false);
    }
  };

  // Build merged data for overlay chart
  const mergedData = (() => {
    if (results.length === 0) return [];
    const dateMap = new Map<string, Record<string, number>>();
    for (const r of results) {
      for (const p of r.equity_curve) {
        if (!dateMap.has(p.date)) dateMap.set(p.date, { date: p.date } as unknown as Record<string, number>);
        const entry = dateMap.get(p.date)!;
        entry[`${r.ticker}_${r.strategy_name}`] = p.equity;
      }
    }
    return Array.from(dateMap.values()).sort((a, b) =>
      String(a.date).localeCompare(String(b.date))
    );
  })();

  return (
    <div>
      <h1 className="page-title">Strategy Comparison</h1>

      <div className="flex-row gap-8 mb-24">
        <button className="btn btn-primary" onClick={loadComparison} disabled={loading}>
          {loading ? <><span className="spinner" /> Loading...</> : "Load All Comparisons"}
        </button>
        <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
          Compares all completed backtests (up to 10)
        </span>
      </div>

      {results.length > 0 && (
        <>
          {/* Overlay Chart */}
          <div className="card">
            <div className="section-title">Equity Curves Overlay</div>
            <div style={{ width: "100%", height: 350 }}>
              <ResponsiveContainer>
                <LineChart data={mergedData} margin={{ top: 5, right: 20, bottom: 5, left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 11, fill: "#6b7280" }}
                    tickFormatter={(v: string) => v.slice(5)}
                    interval="preserveStartEnd"
                  />
                  <YAxis
                    tick={{ fontSize: 11, fill: "#6b7280" }}
                    tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`}
                  />
                  <Tooltip
                    contentStyle={{ background: "#1a1f2e", border: "1px solid #2d3748", borderRadius: 6, fontSize: 12 }}
                  />
                  <Legend
                    wrapperStyle={{ fontSize: 11, color: "#9ca3af" }}
                  />
                  {results.map((r, i) => (
                    <Line
                      key={r.run_id}
                      type="monotone"
                      dataKey={`${r.ticker}_${r.strategy_name}`}
                      stroke={COLORS[i % COLORS.length]}
                      strokeWidth={2}
                      dot={false}
                      name={`${r.ticker} (${r.strategy_name})`}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Summary Table */}
          <div className="card" style={{ padding: 0, overflow: "auto" }}>
            <div className="section-title" style={{ padding: "16px 16px 0" }}>Performance Ranking</div>
            <table className="data-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Ticker</th>
                  <th>Strategy</th>
                  <th>Return %</th>
                  <th>Sharpe</th>
                  <th>Max DD %</th>
                </tr>
              </thead>
              <tbody>
                {[...results]
                  .sort((a, b) => (b.total_return_pct ?? 0) - (a.total_return_pct ?? 0))
                  .map((r, i) => (
                    <tr key={r.run_id}>
                      <td style={{ color: "var(--text-muted)" }}>{i + 1}</td>
                      <td style={{ fontWeight: 600, color: COLORS[results.indexOf(r) % COLORS.length] }}>
                        {r.ticker}
                      </td>
                      <td>{r.strategy_name}</td>
                      <td className={r.total_return_pct >= 0 ? "positive" : "negative"}>
                        {fmt(r.total_return_pct)}%
                      </td>
                      <td>{fmt(r.sharpe_ratio)}</td>
                      <td className="negative">{fmt(r.max_drawdown_pct)}%</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {results.length === 0 && !loading && (
        <div className="empty-state">
          <p>No comparison data yet. Run backtests on stocks first, then come back here to compare.</p>
        </div>
      )}
    </div>
  );
}
