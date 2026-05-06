import { api } from "./client";
import type { CharacterId, User, UserListItem } from "@/lib/types";

export async function listUsers(): Promise<UserListItem[]> {
  const { data } = await api.get<UserListItem[]>("/api/users");
  return data;
}

export async function createUser(name: string): Promise<User> {
  const { data } = await api.post<User>("/api/users", { name });
  return data;
}

export async function updateUser(
  id: string,
  payload: { name?: string; active?: boolean; character_id?: CharacterId },
): Promise<User> {
  const { data } = await api.patch<User>(`/api/users/${id}`, payload);
  return data;
}
