import { api, setToken, clearToken } from "./client";
import type { LoginResponse, UserPublic } from "@/lib/types";

export async function login(password: string): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>("/api/auth/login", { password });
  setToken(data.token);
  return data;
}

export async function me(): Promise<UserPublic> {
  const { data } = await api.get<UserPublic>("/api/auth/me");
  return data;
}

export function logout(): void {
  clearToken();
}
