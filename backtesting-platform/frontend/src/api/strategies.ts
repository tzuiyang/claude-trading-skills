import api from "./client";
import type { Strategy } from "../types";

export async function listStrategies(): Promise<Strategy[]> {
  const { data } = await api.get("/api/strategies");
  return data;
}
