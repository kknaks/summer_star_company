import { api } from "./client";
import type { Card } from "@/lib/types";

export async function listCards(userId?: string): Promise<Card[]> {
  const { data } = await api.get<Card[]>("/api/cards", {
    params: userId ? { user_id: userId } : {},
  });
  return data;
}

export async function createCard(payload: {
  uid: string;
  user_id: string;
  label?: string;
}): Promise<Card> {
  const { data } = await api.post<Card>("/api/cards", payload);
  return data;
}

export async function updateCard(
  id: string,
  payload: { label?: string; active?: boolean },
): Promise<Card> {
  const { data } = await api.patch<Card>(`/api/cards/${id}`, payload);
  return data;
}

export async function scanCard(): Promise<{ uid: string }> {
  const { data } = await api.post<{ uid: string }>("/api/cards/scan");
  return data;
}
