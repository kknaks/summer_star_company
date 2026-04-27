// axios 인스턴스 + JWT 토큰 자동 부착, 401 처리.
// SSOT: docs/spec/admin-web#데이터-페칭, docs/conventions/typescript.

import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from "axios";

const TOKEN_KEY = "ssc_token";

export const getToken = (): string | null => {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
};

export const setToken = (token: string): void => {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_KEY, token);
};

export const clearToken = (): void => {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
};

const baseURL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:48000";

export const api: AxiosInstance = axios.create({
  baseURL,
  timeout: 10_000,
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getToken();
  if (token) {
    config.headers.set("Authorization", `Bearer ${token}`);
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      clearToken();
      if (typeof window !== "undefined" && window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);
