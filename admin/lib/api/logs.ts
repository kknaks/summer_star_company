import { api } from "./client";
import type { AccessLog, AccessLogList } from "@/lib/types";

export interface LogFilters {
  user_id?: string;
  from?: string; // ISO datetime
  to?: string;
  allowed?: boolean;
  include_voided?: boolean;
  cursor?: string;
  limit?: number;
}

export async function listLogs(filters: LogFilters = {}): Promise<AccessLogList> {
  const { data } = await api.get<AccessLogList>("/api/logs", { params: filters });
  return data;
}

export interface CreateLogPayload {
  user_id: string;
  occurred_at: string; // ISO with timezone
  note?: string | null;
}

export async function createLog(payload: CreateLogPayload): Promise<AccessLog> {
  const { data } = await api.post<AccessLog>("/api/logs", payload);
  return data;
}

export interface UpdateLogPayload {
  occurred_at?: string;
  note?: string | null;
  voided?: boolean;
}

export async function updateLog(id: number, payload: UpdateLogPayload): Promise<AccessLog> {
  const { data } = await api.patch<AccessLog>(`/api/logs/${id}`, payload);
  return data;
}

export async function voidLog(id: number): Promise<AccessLog> {
  const { data } = await api.delete<AccessLog>(`/api/logs/${id}`);
  return data;
}
