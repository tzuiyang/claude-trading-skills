import api from "./client";
import type { BacktestSummary, EquityPoint, TradeRecord, SignalPoint } from "../types";

export async function runBacktest(params: {
  ticker: string;
  strategy_name: string;
  params: Record<string, unknown>;
  start_date: string;
  end_date: string;
  initial_capital?: number;
}): Promise<BacktestSummary> {
  const { data } = await api.post("/api/backtests", params);
  return data;
}

export async function getEquityCurve(runId: number): Promise<EquityPoint[]> {
  const { data } = await api.get(`/api/backtests/${runId}/equity`);
  return data;
}

export async function getTrades(runId: number): Promise<TradeRecord[]> {
  const { data } = await api.get(`/api/backtests/${runId}/trades`);
  return data;
}

export async function getSignals(runId: number): Promise<SignalPoint[]> {
  const { data } = await api.get(`/api/backtests/${runId}/signals`);
  return data;
}

export async function compareBacktests(runIds: number[]) {
  const { data } = await api.get("/api/backtests/compare", {
    params: { run_ids: runIds.join(",") },
  });
  return data;
}

export async function deleteBacktest(runId: number): Promise<void> {
  await api.delete(`/api/backtests/${runId}`);
}
