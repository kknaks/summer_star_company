"use client";

import { use, useEffect, useState } from "react";
import { AxiosError } from "axios";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { createCard, listCards, scanCard, updateCard } from "@/lib/api/cards";
import { listUsers } from "@/lib/api/users";
import type { Card, UserListItem } from "@/lib/types";

export default function UserDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [user, setUser] = useState<UserListItem | null>(null);
  const [cards, setCards] = useState<Card[]>([]);
  const [pendingUid, setPendingUid] = useState<string | null>(null);
  const [label, setLabel] = useState("");
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    const us = await listUsers();
    setUser(us.find((u) => u.id === id) ?? null);
    setCards(await listCards(id));
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const onScan = async () => {
    setError(null);
    setScanning(true);
    try {
      const { uid } = await scanCard();
      setPendingUid(uid);
    } catch (err) {
      const ax = err as AxiosError<{ detail: string }>;
      setError(ax.response?.data?.detail ?? "스캔 실패");
    } finally {
      setScanning(false);
    }
  };

  const onSaveCard = async () => {
    if (!pendingUid) return;
    setError(null);
    try {
      await createCard({
        uid: pendingUid,
        user_id: id,
        label: label.trim() || undefined,
      });
      setPendingUid(null);
      setLabel("");
      await load();
    } catch (err) {
      const ax = err as AxiosError<{ detail: string }>;
      setError(ax.response?.data?.detail ?? "저장 실패");
    }
  };

  const onToggleCard = async (c: Card) => {
    await updateCard(c.id, { active: !c.active });
    await load();
  };

  if (!user) {
    return <p className="text-sm text-neutral-500">로딩...</p>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">{user.name}</h2>
        <p className="text-sm text-neutral-500">
          역할: {user.role} / {user.active ? "활성" : "비활성"}
        </p>
      </div>

      <div className="bg-white border rounded-lg p-4 space-y-3">
        <h3 className="font-semibold">카드 등록</h3>
        {pendingUid ? (
          <div className="space-y-2">
            <p className="text-sm">
              감지된 UID: <code className="font-mono">{pendingUid}</code>
            </p>
            <div className="flex gap-2">
              <Input
                placeholder="라벨 (선택, 예: 메인)"
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                className="max-w-xs"
              />
              <Button onClick={onSaveCard}>저장</Button>
              <Button
                variant="outline"
                onClick={() => {
                  setPendingUid(null);
                  setLabel("");
                }}
              >
                취소
              </Button>
            </div>
          </div>
        ) : (
          <Button onClick={onScan} disabled={scanning}>
            {scanning ? "30초 내 카드 태그..." : "카드 추가 (등록 리더)"}
          </Button>
        )}
        {error && <p className="text-sm text-red-600">{error}</p>}
      </div>

      <div className="bg-white border rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-neutral-50 text-left">
            <tr>
              <th className="px-3 py-2">UID</th>
              <th className="px-3 py-2">라벨</th>
              <th className="px-3 py-2">등록</th>
              <th className="px-3 py-2">활성</th>
              <th className="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {cards.map((c) => (
              <tr key={c.id} className="border-t">
                <td className="px-3 py-2 font-mono text-xs">{c.uid}</td>
                <td className="px-3 py-2">{c.label ?? "—"}</td>
                <td className="px-3 py-2 font-mono text-xs">
                  {new Date(c.registered_at).toLocaleDateString("ko-KR", {
                    timeZone: "Asia/Seoul",
                  })}
                </td>
                <td className="px-3 py-2">
                  <span
                    className={c.active ? "text-green-700" : "text-neutral-500"}
                  >
                    {c.active ? "활성" : "비활성"}
                  </span>
                </td>
                <td className="px-3 py-2 text-right">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onToggleCard(c)}
                  >
                    {c.active ? "분실 처리" : "재활성"}
                  </Button>
                </td>
              </tr>
            ))}
            {cards.length === 0 && (
              <tr>
                <td colSpan={5} className="px-3 py-8 text-center text-neutral-500">
                  카드 없음
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
