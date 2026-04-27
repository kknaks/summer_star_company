import { api } from "./client";
import type { AccessLogList } from "@/lib/types";

export interface LogFilters {
  user_id?: string;
  from?: string; // ISO datetime
  to?: string;
  allowed?: boolean;
  cursor?: string;
  limit?: number;
}

export async function listLogs(filters: LogFilters = {}): Promise<AccessLogList> {
  const { data } = await api.get<AccessLogList>("/api/logs", { params: filters });
  return data;
}
