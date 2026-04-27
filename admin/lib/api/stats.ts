import { api } from "./client";
import type { DailyStat, MonthlyStat } from "@/lib/types";

export async function dailyStats(
  user_id: string,
  year: number,
  month: number,
): Promise<DailyStat[]> {
  const { data } = await api.get<DailyStat[]>("/api/stats/daily", {
    params: { user_id, year, month },
  });
  return data;
}

export async function monthlyStats(
  user_id: string,
  year: number,
): Promise<MonthlyStat[]> {
  const { data } = await api.get<MonthlyStat[]>("/api/stats/monthly", {
    params: { user_id, year },
  });
  return data;
}
