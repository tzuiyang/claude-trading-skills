import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Scatter,
} from "recharts";
import type { PricePoint, SignalPoint } from "../../types";

interface Props {
  prices: PricePoint[];
  signals: SignalPoint[];
  sliceEnd?: number;
}

export default function PriceSignalChart({ prices, signals, sliceEnd }: Props) {
  const signalMap = new Map(signals.map(s => [s.date, s]));

  const visible = sliceEnd != null ? prices.slice(0, sliceEnd + 1) : prices;

  const data = visible.map(p => ({
    date: p.date,
    close: p.close,
    buyPrice: signalMap.get(p.date)?.signal === "buy" ? p.close : undefined,
    sellPrice: signalMap.get(p.date)?.signal === "sell" ? p.close : undefined,
  }));

  return (
    <div style={{ width: "100%", height: 300 }}>
      <ResponsiveContainer>
        <ComposedChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: "#6b7280" }}
            tickFormatter={(v: string) => v.slice(5)}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fontSize: 11, fill: "#6b7280" }}
            tickFormatter={(v: number) => `$${v.toFixed(0)}`}
            domain={["auto", "auto"]}
          />
          <Tooltip
            contentStyle={{ background: "#1a1f2e", border: "1px solid #2d3748", borderRadius: 6, fontSize: 12 }}
            formatter={(v: unknown, name: unknown) => {
              const val = Number(v);
              const label = name === "buyPrice" ? "Buy" : name === "sellPrice" ? "Sell" : "Close";
              return [isNaN(val) ? "—" : `$${val.toFixed(2)}`, label];
            }}
          />
          <Line type="monotone" dataKey="close" stroke="#6b7280" strokeWidth={1.5} dot={false} />
          <Scatter dataKey="buyPrice" fill="#22c55e" shape="triangle" />
          <Scatter dataKey="sellPrice" fill="#ef4444" shape="triangle" />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
