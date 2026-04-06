import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  ReferenceLine,
} from "recharts";
import type { EquityPoint } from "../../types";

interface Props {
  data: EquityPoint[];
  sliceEnd?: number;
  color?: string;
  label?: string;
}

export default function EquityChart({ data, sliceEnd, color = "#38bdf8", label = "Equity" }: Props) {
  const visible = sliceEnd != null ? data.slice(0, sliceEnd + 1) : data;
  const initial = visible.length > 0 ? visible[0].equity : 0;

  return (
    <div style={{ width: "100%", height: 280 }}>
      <ResponsiveContainer>
        <LineChart data={visible} margin={{ top: 5, right: 20, bottom: 5, left: 20 }}>
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
            domain={["auto", "auto"]}
          />
          <Tooltip
            contentStyle={{ background: "#1a1f2e", border: "1px solid #2d3748", borderRadius: 6, fontSize: 12 }}
            labelStyle={{ color: "#9ca3af" }}
            formatter={(v: unknown) => [`$${Number(v).toLocaleString(undefined, { maximumFractionDigits: 0 })}`, label]}
          />
          <ReferenceLine y={initial} stroke="#4b5563" strokeDasharray="3 3" />
          <Line type="monotone" dataKey="equity" stroke={color} strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
