"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AxiosError } from "axios";

import Icon from "@/components/pixel/Icon";
import StatusBar from "@/components/win98/StatusBar";
import TitleBar from "@/components/win98/TitleBar";
import { login } from "@/lib/api/auth";

export default function LoginPage() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(password);
      router.replace("/logs");
    } catch (err) {
      const ax = err as AxiosError<{ detail: string }>;
      setError(ax.response?.data?.detail ?? "로그인 실패");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="desktop">
      <div style={{ width: "100%", maxWidth: 1100 }}>
        <div className="window login-dialog">
          <TitleBar title="관리자 로그인" icon="key" />
          <div className="window-body">
            <div
              style={{
                display: "flex",
                gap: 12,
                alignItems: "center",
                background: "#fff",
                padding: 12,
                marginBottom: 12,
                boxShadow:
                  "inset 1px 1px 0 #404040, inset -1px -1px 0 #fff",
              }}
            >
              <div style={{ flexShrink: 0 }}>
                <Icon name="key" scale={3} />
              </div>
              <div style={{ fontSize: 13 }}>
                <div style={{ fontWeight: 600, marginBottom: 6 }}>
                  Summer Star Admin
                </div>
                <div>관리자 비밀번호를 입력하세요.</div>
              </div>
            </div>

            <form
              onSubmit={onSubmit}
              style={{ display: "flex", flexDirection: "column", gap: 8 }}
            >
              <label style={{ fontSize: 13, fontWeight: 600 }}>비밀번호</label>
              <input
                type="password"
                className="input"
                placeholder="••••••••"
                autoFocus
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              {error && (
                <div
                  style={{
                    fontSize: 13,
                    color: "var(--accent-red)",
                    fontWeight: 700,
                  }}
                >
                  ⚠ {error}
                </div>
              )}
              <div
                style={{
                  display: "flex",
                  gap: 8,
                  justifyContent: "flex-end",
                  marginTop: 8,
                }}
              >
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={submitting || !password}
                >
                  {submitting ? (
                    <span>
                      접속중<span className="blink">_</span>
                    </span>
                  ) : (
                    "확인"
                  )}
                </button>
                <button
                  type="button"
                  className="btn"
                  onClick={() => setPassword("")}
                >
                  취소
                </button>
              </div>
            </form>
          </div>
          <StatusBar
            left={<span>준비됨</span>}
            right={<span className="mono">SSC v1.0</span>}
          />
        </div>
      </div>
    </div>
  );
}
