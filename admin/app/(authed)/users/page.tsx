"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AxiosError } from "axios";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { createUser, listUsers, updateUser } from "@/lib/api/users";
import type { UserListItem } from "@/lib/types";

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
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">사용자</h2>

      <form
        onSubmit={onAdd}
        className="flex gap-2 bg-white border rounded-lg p-3"
      >
        <Input
          placeholder="이름"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="max-w-xs"
        />
        <Button type="submit" disabled={submitting || !name.trim()}>
          추가
        </Button>
        {error && <p className="text-sm text-red-600 self-center">{error}</p>}
      </form>

      <div className="bg-white border rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-neutral-50 text-left">
            <tr>
              <th className="px-3 py-2">이름</th>
              <th className="px-3 py-2">역할</th>
              <th className="px-3 py-2">카드</th>
              <th className="px-3 py-2">최근 출입</th>
              <th className="px-3 py-2">활성</th>
              <th className="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-t">
                <td className="px-3 py-2 font-medium">
                  <Link href={`/users/${u.id}`} className="hover:underline">
                    {u.name}
                  </Link>
                </td>
                <td className="px-3 py-2">{u.role}</td>
                <td className="px-3 py-2">{u.card_count}장</td>
                <td className="px-3 py-2 font-mono text-xs">
                  {u.last_access_at
                    ? new Date(u.last_access_at).toLocaleString("ko-KR", {
                        timeZone: "Asia/Seoul",
                      })
                    : "—"}
                </td>
                <td className="px-3 py-2">
                  <span
                    className={
                      u.active
                        ? "text-green-700"
                        : "text-neutral-500"
                    }
                  >
                    {u.active ? "활성" : "비활성"}
                  </span>
                </td>
                <td className="px-3 py-2 text-right">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onToggleActive(u)}
                  >
                    {u.active ? "비활성화" : "활성화"}
                  </Button>
                </td>
              </tr>
            ))}
            {users.length === 0 && (
              <tr>
                <td colSpan={6} className="px-3 py-8 text-center text-neutral-500">
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
