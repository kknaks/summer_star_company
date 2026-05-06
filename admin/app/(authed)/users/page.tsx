"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AxiosError } from "axios";

import Avatar from "@/components/pixel/Avatar";
import { createUser, listUsers, updateUser } from "@/lib/api/users";
import type { UserListItem } from "@/lib/types";

function fmtDate(iso: string) {
  return new Date(iso).toLocaleString("ko-KR", { timeZone: "Asia/Seoul" });
}

export default function UsersPage() {
  const [users, setUsers] = useState<UserListItem[]>([]);
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const load = async () => {
    setUsers(await listUsers());
  };

  useEffect(() => {
    load();
  }, []);

  const onAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await createUser(name.trim());
      setName("");
      await load();
    } catch (err) {
      const ax = err as AxiosError<{ detail: string }>;
      setError(ax.response?.data?.detail ?? "추가 실패");
    } finally {
      setSubmitting(false);
    }
  };

  const onToggleActive = async (u: UserListItem) => {
    await updateUser(u.id, { active: !u.active });
    await load();
  };

  return (
    <div>
      <div className="toolbar">
        <form
          onSubmit={onAdd}
          style={{
            display: "flex",
            gap: 8,
            alignItems: "center",
            flexWrap: "wrap",
          }}
        >
          <input
            className="input"
            placeholder="이름 입력"
            value={name}
            onChange={(e) => setName(e.target.value)}
            style={{ width: 160 }}
          />
          <button
            type="submit"
            className="btn"
            disabled={submitting || !name.trim()}
          >
            ＋ 직원 추가
          </button>
          {error && (
            <span
              style={{ fontSize: 13, color: "var(--accent-red)" }}
            >
              {error}
            </span>
          )}
        </form>
        <span className="sep hide-mobile" />
        <span className="hide-mobile mono" style={{ fontSize: 13 }}>
          {users.length}명
        </span>
      </div>

      <div
        style={{
          display: "flex",
          gap: 12,
          marginTop: 12,
          flexWrap: "wrap",
        }}
      >
        {users.map((u) => (
          <Link
            key={u.id}
            href={`/users/${u.id}`}
            className="avatar-card"
            style={{
              flex: "1 1 220px",
              cursor: "pointer",
              textDecoration: "none",
              color: "inherit",
            }}
          >
            <Avatar characterId={u.character_id} seed={u.id} scale={3} />
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: 4,
                flex: 1,
              }}
            >
              <div style={{ fontWeight: 600 }}>{u.name}</div>
              <div className="text-muted" style={{ fontSize: 12 }}>
                {u.role === "admin" ? "★ 관리자" : "○ 직원"} · 카드{" "}
                {u.card_count}장
              </div>
              <div className="text-muted mono" style={{ fontSize: 12 }}>
                {u.last_access_at
                  ? fmtDate(u.last_access_at).slice(5)
                  : "—"}
              </div>
              <div style={{ marginTop: 4 }}>
                {u.active ? (
                  <span className="badge badge-ok">
                    <span className="dot" />
                    활성
                  </span>
                ) : (
                  <span className="badge badge-off">
                    <span className="dot" />
                    비활성
                  </span>
                )}
              </div>
            </div>
          </Link>
        ))}
      </div>

      <div
        className="win-in"
        style={{ padding: 2, overflowX: "auto", marginTop: 12 }}
      >
        <table className="pixel-table">
          <thead>
            <tr>
              <th>이름</th>
              <th className="hide-mobile">역할</th>
              <th className="hide-mobile">카드</th>
              <th className="hide-mobile">최근 출입</th>
              <th>활성</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>
                  <Link
                    href={`/users/${u.id}`}
                    className="row-link"
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 8,
                    }}
                  >
                    <Avatar
                      characterId={u.character_id}
                      seed={u.id}
                      scale={1}
                    />
                    {u.name}
                  </Link>
                </td>
                <td className="hide-mobile">{u.role}</td>
                <td className="hide-mobile mono">{u.card_count}장</td>
                <td className="hide-mobile mono" style={{ fontSize: 12 }}>
                  {u.last_access_at ? fmtDate(u.last_access_at) : "—"}
                </td>
                <td>
                  {u.active ? (
                    <span className="badge badge-ok">
                      <span className="dot" />
                      활성
                    </span>
                  ) : (
                    <span className="badge badge-off">
                      <span className="dot" />
                      비활성
                    </span>
                  )}
                </td>
                <td style={{ textAlign: "right" }}>
                  <button
                    type="button"
                    className="btn"
                    style={{
                      minWidth: 0,
                      padding: "2px 8px",
                      minHeight: 24,
                      fontSize: 12,
                    }}
                    onClick={() => onToggleActive(u)}
                  >
                    {u.active ? "비활성화" : "활성화"}
                  </button>
                </td>
              </tr>
            ))}
            {users.length === 0 && (
              <tr>
                <td
                  colSpan={6}
                  style={{
                    padding: "32px 12px",
                    textAlign: "center",
                    color: "var(--win-bg-darker)",
                  }}
                >
                  사용자 없음
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
