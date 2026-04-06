import api from "./client";
import type { StockWithMetrics, PricePoint, BacktestSummary } from "../types";

export async function listStocks(): Promise<StockWithMetrics[]> {
  const { data } = await api.get("/api/stocks");
  return data;
}

export async function addStock(ticker: string): Promise<StockWithMetrics> {
  const { data } = await api.post("/api/stocks", { ticker });
  return data;
}

export async function getStockPrices(ticker: string, start?: string, end?: string): Promise<PricePoint[]> {
  const params: Record<string, string> = {};
  if (start) params.start = start;
  if (end) params.end = end;
  const { data } = await api.get(`/api/stocks/${ticker}/prices`, { params });
  return data;
}

export async function getStockBacktests(ticker: string): Promise<BacktestSummary[]> {
  const { data } = await api.get(`/api/stocks/${ticker}/backtests`);
  return data;
}
