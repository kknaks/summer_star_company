"use client";

import { useEffect, useState } from "react";
import { AxiosError } from "axios";

import Avatar from "@/components/pixel/Avatar";
import Icon from "@/components/pixel/Icon";
import Select from "@/components/win98/Select";
import TitleBar from "@/components/win98/TitleBar";
import { me } from "@/lib/api/auth";
import {
  createLog,
  listLogs,
  updateLog,
  voidLog,
} from "@/lib/api/logs";
import { listUsers } from "@/lib/api/users";
import type { AccessLog, User, UserPublic } from "@/lib/types";

function fmtDate(iso: string) {
  return new Date(iso).toLocaleString("ko-KR", { timeZone: "Asia/Seoul" });
}

// "YYYY-MM-DDTHH:mm" 로컬 입력값 → ISO with offset (KST 가정)
function localToIso(local: string): string {
  // datetime-local 의 값은 timezone 없음. KST 로 해석.
  return `${local}:00+09:00`;
}

// ISO → "YYYY-MM-DDTHH:mm" KST
function isoToLocal(iso: string): string {
  const d = new Date(iso);
  const kstMs = d.getTime() + 9 * 3600 * 1000;
  return new Date(kstMs).toISOString().slice(0, 16);
}

interface AddModalProps {
  users: User[];
  onSubmit: (payload: { user_id: string; occurred_at: string; note: string | null }) => Promise<void>;
  onClose: () => void;
}

function AddManualModal({ users, onSubmit, onClose }: AddModalProps) {
  const activeUsers = users.filter((u) => u.active);
  const [userId, setUserId] = useState(activeUsers[0]?.id ?? "");
  const [occurredAt, setOccurredAt] = useState(() => {
    const now = new Date();
    const kstMs = now.getTime() + 9 * 3600 * 1000;
    return new Date(kstMs).toISOString().slice(0, 16);
  });
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userId) return;
    setSubmitting(true);
    setErr(null);
    try {
      await onSubmit({
        user_id: userId,
        occurred_at: localToIso(occurredAt),
        note: note.trim() || null,
      });
      onClose();
    } catch (error) {
      const ax = error as AxiosError<{ detail: string }>;
      setErr(ax.response?.data?.detail ?? "추가 실패");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="window"
        style={{ width: "min(420px, 100%)" }}
        onClick={(e) => e.stopPropagation()}
      >
        <TitleBar title="탭 수동 추가" icon="log" onClose={onClose} />
        <form onSubmit={submit} style={{ padding: 12 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <span style={{ fontSize: 13 }}>사용자</span>
              <Select<string>
                value={userId}
                onChange={setUserId}
                options={activeUsers.map((u) => ({ value: u.id, label: u.name }))}
                ariaLabel="사용자"
              />
            </label>
            <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <span style={{ fontSize: 13 }}>시각 (KST)</span>
              <input
                type="datetime-local"
                className="input"
                value={occurredAt}
                onChange={(e) => setOccurredAt(e.target.value)}
                required
              />
            </label>
            <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <span style={{ fontSize: 13 }}>메모 (선택)</span>
              <input
                type="text"
                className="input"
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="누락 보정 사유 등"
              />
            </label>
            {err && (
              <span style={{ fontSize: 12, color: "var(--accent-red)" }}>{err}</span>
            )}
            <div
              style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: 4 }}
            >
              <button type="button" className="btn" onClick={onClose}>
                취소
              </button>
              <button
                type="submit"
                className="btn"
                disabled={submitting || !userId}
              >
                {submitting ? "..." : "추가"}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}

interface EditModalProps {
  log: AccessLog;
  onSubmit: (payload: {
    occurred_at?: string;
    note?: string | null;
  }) => Promise<void>;
  onClose: () => void;
}

function EditManualModal({ log, onSubmit, onClose }: EditModalProps) {
  const [occurredAt, setOccurredAt] = useState(isoToLocal(log.occurred_at));
  const [note, setNote] = useState(log.note ?? "");
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setErr(null);
    try {
      await onSubmit({
        occurred_at: localToIso(occurredAt),
        note: note.trim() || null,
      });
      onClose();
    } catch (error) {
      const ax = error as AxiosError<{ detail: string }>;
      setErr(ax.response?.data?.detail ?? "수정 실패");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="window"
        style={{ width: "min(420px, 100%)" }}
        onClick={(e) => e.stopPropagation()}
      >
        <TitleBar title="수동 탭 수정" icon="log" onClose={onClose} />
        <form onSubmit={submit} style={{ padding: 12 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <span style={{ fontSize: 13 }}>시각 (KST)</span>
              <input
                type="datetime-local"
                className="input"
                value={occurredAt}
                onChange={(e) => setOccurredAt(e.target.value)}
                required
              />
            </label>
            <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <span style={{ fontSize: 13 }}>메모</span>
              <input
                type="text"
                className="input"
                value={note}
                onChange={(e) => setNote(e.target.value)}
              />
            </label>
            {err && (
              <span style={{ fontSize: 12, color: "var(--accent-red)" }}>{err}</span>
            )}
            <div
              style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: 4 }}
            >
              <button type="button" className="btn" onClick={onClose}>
                취소
              </button>
              <button type="submit" className="btn" disabled={submitting}>
                {submitting ? "..." : "저장"}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function LogsPage() {
  const [items, setItems] = useState<AccessLog[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [usersById, setUsersById] = useState<Record<string, User>>({});
  const [usersList, setUsersList] = useState<User[]>([]);
  const [allowedFilter, setAllowedFilter] = useState<"all" | "true" | "false">(
    "all",
  );
  const [includeVoided, setIncludeVoided] = useState(false);
  const [meUser, setMeUser] = useState<UserPublic | null>(null);
  const [showAdd, setShowAdd] = useState(false);
  const [editing, setEditing] = useState<AccessLog | null>(null);

  const isAdmin = meUser?.role === "admin";

  const load = async (cursor?: string) => {
    setLoading(true);
    try {
      const params: {
        cursor?: string;
        allowed?: boolean;
        include_voided?: boolean;
        limit: number;
      } = { limit: 50 };
      if (cursor) params.cursor = cursor;
      if (allowedFilter !== "all") params.allowed = allowedFilter === "true";
      if (includeVoided) params.include_voided = true;
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
    listUsers().then((us) => {
      setUsersList(us);
      setUsersById(Object.fromEntries(us.map((u) => [u.id, u])));
    });
    me().then(setMeUser).catch(() => setMeUser(null));
  }, []);

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allowedFilter, includeVoided]);

  const onAdd = async (payload: {
    user_id: string;
    occurred_at: string;
    note: string | null;
  }) => {
    await createLog(payload);
    await load();
  };

  const onEdit = async (
    log: AccessLog,
    payload: { occurred_at?: string; note?: string | null },
  ) => {
    await updateLog(log.id, payload);
    await load();
  };

  const onToggleVoid = async (log: AccessLog) => {
    if (log.voided) {
      await updateLog(log.id, { voided: false });
    } else {
      await voidLog(log.id);
    }
    await load();
  };

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
        <label
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 4,
            fontSize: 13,
          }}
        >
          <input
            type="checkbox"
            checked={includeVoided}
            onChange={(e) => setIncludeVoided(e.target.checked)}
          />
          무효 포함
        </label>
        {isAdmin && (
          <>
            <span className="sep" />
            <button
              type="button"
              className="btn"
              onClick={() => setShowAdd(true)}
            >
              ＋ 탭 추가
            </button>
          </>
        )}
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
              <th className="hide-mobile">출처</th>
              <th>결과</th>
              {isAdmin && <th></th>}
            </tr>
          </thead>
          <tbody>
            {items.map((log) => {
              const u = log.user_id ? usersById[log.user_id] : null;
              const rowStyle = log.voided
                ? { opacity: 0.5, textDecoration: "line-through" as const }
                : undefined;
              return (
                <tr key={log.id} style={rowStyle}>
                  <td className="mono">
                    {fmtDate(log.occurred_at)}
                    {log.note && (
                      <div
                        className="text-muted"
                        style={{ fontSize: 11, marginTop: 2 }}
                      >
                        ※ {log.note}
                      </div>
                    )}
                  </td>
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
                  <td className="hide-mobile">
                    {log.source === "manual" ? (
                      <span className="badge badge-off">
                        <span className="dot" />
                        수동
                      </span>
                    ) : (
                      <span className="mono" style={{ fontSize: 12 }}>
                        {log.uid}
                      </span>
                    )}
                  </td>
                  <td>
                    {log.voided ? (
                      <span className="badge badge-off">
                        <span className="dot" />
                        무효
                      </span>
                    ) : log.allowed ? (
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
                  {isAdmin && (
                    <td style={{ textAlign: "right", whiteSpace: "nowrap" }}>
                      {log.source === "manual" && !log.voided && (
                        <button
                          type="button"
                          className="btn"
                          style={{
                            minWidth: 0,
                            padding: "2px 8px",
                            minHeight: 24,
                            fontSize: 12,
                            marginRight: 4,
                          }}
                          onClick={() => setEditing(log)}
                        >
                          수정
                        </button>
                      )}
                      <button
                        type="button"
                        className="btn"
                        style={{
                          minWidth: 0,
                          padding: "2px 8px",
                          minHeight: 24,
                          fontSize: 12,
                        }}
                        onClick={() => onToggleVoid(log)}
                      >
                        {log.voided ? "복구" : "무효화"}
                      </button>
                    </td>
                  )}
                </tr>
              );
            })}
            {items.length === 0 && !loading && (
              <tr>
                <td
                  colSpan={isAdmin ? 5 : 4}
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

      {showAdd && (
        <AddManualModal
          users={usersList}
          onSubmit={onAdd}
          onClose={() => setShowAdd(false)}
        />
      )}
      {editing && (
        <EditManualModal
          log={editing}
          onSubmit={(p) => onEdit(editing, p)}
          onClose={() => setEditing(null)}
        />
      )}
    </div>
  );
}
