"use client";

import { useEffect, useState } from "react";

import Avatar from "@/components/pixel/Avatar";
import Icon from "@/components/pixel/Icon";
import Select from "@/components/win98/Select";
import { listLogs } from "@/lib/api/logs";
import { listUsers } from "@/lib/api/users";
import type { AccessLog, User } from "@/lib/types";

function fmtDate(iso: string) {
  return new Date(iso).toLocaleString("ko-KR", { timeZone: "Asia/Seoul" });
}

export default function LogsPage() {
  const [items, setItems] = useState<AccessLog[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [users, setUsers] = useState<Record<string, User>>({});
  const [allowedFilter, setAllowedFilter] = useState<"all" | "true" | "false">(
    "all",
  );

  const load = async (cursor?: string) => {
    setLoading(true);
    try {
      const params: { cursor?: string; allowed?: boolean; limit: number } = {
        limit: 50,
      };
      if (cursor) params.cursor = cursor;
      if (allowedFilter !== "all") params.allowed = allowedFilter === "true";
      const res = await listLogs(params);
      if (cursor) {
        setItems((prev) => [...prev, ...res.items]);
      } else {
        setItems(res.items);
      }
      setNextCursor(res.next_cursor);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    listUsers().then((us) =>
      setUsers(Object.fromEntries(us.map((u) => [u.id, u]))),
    );
  }, []);

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allowedFilter]);

  return (
    <div>
      <div className="toolbar">
        <button
          type="button"
          className="btn btn-tool"
          onClick={() => load()}
          disabled={loading}
          title="새로고침"
        >
          <Icon name="clock" scale={1} />
          <span className="lbl">새로고침</span>
        </button>
        <span className="sep" />
        <span style={{ fontSize: 13 }}>필터:</span>
        <Select<"all" | "true" | "false">
          value={allowedFilter}
          onChange={setAllowedFilter}
          options={[
            { value: "all", label: "전체" },
            { value: "true", label: "허용만" },
            { value: "false", label: "거부만" },
          ]}
          ariaLabel="결과 필터"
          style={{ minWidth: 100 }}
        />
        <span className="sep hide-mobile" />
        <span className="hide-mobile mono" style={{ fontSize: 13 }}>
          총 {items.length}건
        </span>
      </div>

      <div
        className="win-in"
        style={{ padding: 2, marginTop: 4, overflowX: "auto" }}
      >
        <table className="pixel-table">
          <thead>
            <tr>
              <th>시각 (KST)</th>
              <th>사용자</th>
              <th className="hide-mobile">UID</th>
              <th>결과</th>
            </tr>
          </thead>
          <tbody>
            {items.map((log) => {
              const u = log.user_id ? users[log.user_id] : null;
              return (
                <tr key={log.id}>
                  <td className="mono">{fmtDate(log.occurred_at)}</td>
                  <td>
                    <span
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: 8,
                      }}
                    >
                      {u && (
                        <Avatar
                          characterId={u.character_id}
                          seed={u.id}
                          scale={1}
                        />
                      )}
                      <span>
                        {u ? (
                          u.name
                        ) : (
                          <span className="text-muted">unknown</span>
                        )}
                      </span>
                    </span>
                  </td>
                  <td className="mono hide-mobile">{log.uid}</td>
                  <td>
                    {log.allowed ? (
                      <span className="badge badge-ok">
                        <span className="dot" />
                        허용
                      </span>
                    ) : (
                      <span className="badge badge-deny">
                        <span className="dot" />
                        거부
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
            {items.length === 0 && !loading && (
              <tr>
                <td
                  colSpan={4}
                  style={{
                    padding: "32px 12px",
                    textAlign: "center",
                    color: "var(--win-bg-darker)",
                  }}
                >
                  로그 없음
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginTop: 12,
        }}
      >
        <span className="text-muted" style={{ fontSize: 13 }}>
          최신순
        </span>
        {nextCursor && (
          <button
            type="button"
            className="btn"
            onClick={() => load(nextCursor)}
            disabled={loading}
          >
            {loading ? "..." : "더 보기"}
          </button>
        )}
      </div>
    </div>
  );
}
