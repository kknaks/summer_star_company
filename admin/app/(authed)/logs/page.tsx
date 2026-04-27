"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { listLogs } from "@/lib/api/logs";
import { listUsers } from "@/lib/api/users";
import type { AccessLog, User } from "@/lib/types";

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
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <h2 className="text-lg font-semibold flex-1">출입 로그</h2>
        <select
          className="border rounded px-2 py-1 text-sm bg-white"
          value={allowedFilter}
          onChange={(e) =>
            setAllowedFilter(e.target.value as "all" | "true" | "false")
          }
        >
          <option value="all">전체</option>
          <option value="true">허용만</option>
          <option value="false">거부만</option>
        </select>
      </div>

      <div className="bg-white border rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-neutral-50 text-left">
            <tr>
              <th className="px-3 py-2">시각 (KST)</th>
              <th className="px-3 py-2">사용자</th>
              <th className="px-3 py-2">UID</th>
              <th className="px-3 py-2">결과</th>
            </tr>
          </thead>
          <tbody>
            {items.map((log) => (
              <tr key={log.id} className="border-t">
                <td className="px-3 py-2 font-mono text-xs">
                  {new Date(log.occurred_at).toLocaleString("ko-KR", {
                    timeZone: "Asia/Seoul",
                  })}
                </td>
                <td className="px-3 py-2">
                  {log.user_id
                    ? users[log.user_id]?.name ?? log.user_id.slice(0, 8)
                    : "—"}
                </td>
                <td className="px-3 py-2 font-mono text-xs">{log.uid}</td>
                <td className="px-3 py-2">
                  <span
                    className={
                      log.allowed
                        ? "text-green-700 font-medium"
                        : "text-red-700 font-medium"
                    }
                  >
                    {log.allowed ? "허용" : "거부"}
                  </span>
                </td>
              </tr>
            ))}
            {items.length === 0 && !loading && (
              <tr>
                <td colSpan={4} className="px-3 py-8 text-center text-neutral-500">
                  로그 없음
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="flex justify-center">
        {nextCursor ? (
          <Button
            variant="outline"
            onClick={() => load(nextCursor)}
            disabled={loading}
          >
            {loading ? "..." : "더 보기"}
          </Button>
        ) : items.length > 0 ? (
          <p className="text-sm text-neutral-500">끝</p>
        ) : null}
      </div>
    </div>
  );
}
