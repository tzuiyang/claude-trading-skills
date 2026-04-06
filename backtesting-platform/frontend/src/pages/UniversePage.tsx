import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { listStocks, addStock } from "../api/stocks";
import type { StockWithMetrics } from "../types";

type SortKey = keyof StockWithMetrics;
type SortDir = "asc" | "desc";

function fmt(val: number | null | undefined, decimals = 2): string {
  if (val == null) return "—";
  return val.toFixed(decimals);
}

export default function UniversePage() {
  const [stocks, setStocks] = useState<StockWithMetrics[]>([]);
  const [loading, setLoading] = useState(true);
  const [tickerInput, setTickerInput] = useState("");
  const [adding, setAdding] = useState(false);
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("ticker");
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const navigate = useNavigate();

  const fetchStocks = async () => {
    setLoading(true);
    try {
      setStocks(await listStocks());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchStocks(); }, []);

  const handleAdd = async () => {
    if (!tickerInput.trim()) return;
    setAdding(true);
    try {
      await addStock(tickerInput.trim());
      setTickerInput("");
      await fetchStocks();
    } finally {
      setAdding(false);
    }
  };

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(d => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  };

  const filtered = useMemo(() => {
    let list = stocks;
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(
        s =>
          s.ticker.toLowerCase().includes(q) ||
          (s.name && s.name.toLowerCase().includes(q)) ||
          (s.sector && s.sector.toLowerCase().includes(q))
      );
    }
    list = [...list].sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (av == null && bv == null) return 0;
      if (av == null) return 1;
      if (bv == null) return -1;
      if (typeof av === "string" && typeof bv === "string") {
        return sortDir === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
      }
      const diff = (av as number) - (bv as number);
      return sortDir === "asc" ? diff : -diff;
    });
    return list;
  }, [stocks, search, sortKey, sortDir]);

  const arrow = (key: SortKey) =>
    sortKey === key ? (sortDir === "asc" ? " ↑" : " ↓") : "";

  return (
    <div>
      <h1 className="page-title">Stock Universe</h1>

      <div className="flex-row gap-8 mb-16">
        <input
          className="input"
          placeholder="Add ticker (e.g. AAPL)"
          value={tickerInput}
          onChange={e => setTickerInput(e.target.value.toUpperCase())}
          onKeyDown={e => e.key === "Enter" && handleAdd()}
          style={{ width: 200 }}
        />
        <button className="btn btn-primary" onClick={handleAdd} disabled={adding}>
          {adding ? <span className="spinner" /> : "Add Stock"}
        </button>
        <div style={{ flex: 1 }} />
        <input
          className="input"
          placeholder="Search stocks..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ width: 240 }}
        />
      </div>

      {loading ? (
        <div className="empty-state"><span className="spinner" /></div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          <p>No stocks yet. Add a ticker above to get started.</p>
        </div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "auto" }}>
          <table className="data-table">
            <thead>
              <tr>
                <th onClick={() => handleSort("ticker")}>Ticker{arrow("ticker")}</th>
                <th onClick={() => handleSort("name")}>Name{arrow("name")}</th>
                <th onClick={() => handleSort("sector")}>Sector{arrow("sector")}</th>
                <th onClick={() => handleSort("strategies_tested")}>Strategies{arrow("strategies_tested")}</th>
                <th onClick={() => handleSort("total_return_pct")}>Return %{arrow("total_return_pct")}</th>
                <th onClick={() => handleSort("max_drawdown_pct")}>Max DD %{arrow("max_drawdown_pct")}</th>
                <th onClick={() => handleSort("win_rate_pct")}>Win Rate %{arrow("win_rate_pct")}</th>
                <th onClick={() => handleSort("sharpe_ratio")}>Sharpe{arrow("sharpe_ratio")}</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(s => (
                <tr
                  key={s.id}
                  className="clickable"
                  onClick={() => navigate(`/stock/${s.ticker}`)}
                  style={{ cursor: "pointer" }}
                >
                  <td style={{ fontWeight: 600, color: "var(--accent)" }}>{s.ticker}</td>
                  <td style={{ color: "var(--text-secondary)", maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis" }}>
                    {s.name || "—"}
                  </td>
                  <td style={{ color: "var(--text-muted)" }}>{s.sector || "—"}</td>
                  <td>{s.strategies_tested}</td>
                  <td className={s.total_return_pct != null ? (s.total_return_pct >= 0 ? "positive" : "negative") : ""}>
                    {fmt(s.total_return_pct)}
                  </td>
                  <td className="negative">{fmt(s.max_drawdown_pct)}</td>
                  <td>{fmt(s.win_rate_pct)}</td>
                  <td className={s.sharpe_ratio != null ? (s.sharpe_ratio >= 0 ? "positive" : "negative") : ""}>
                    {fmt(s.sharpe_ratio)}
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
