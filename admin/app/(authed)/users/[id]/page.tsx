"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import { AxiosError } from "axios";

import Avatar from "@/components/pixel/Avatar";
import { CHARACTER_LIST } from "@/components/pixel/characters";
import { createCard, listCards, scanCard, updateCard } from "@/lib/api/cards";
import { listUsers, updateUser } from "@/lib/api/users";
import type { CharacterId, Card, UserListItem } from "@/lib/types";

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString("ko-KR", { timeZone: "Asia/Seoul" });
}

export default function UserDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [user, setUser] = useState<UserListItem | null>(null);
  const [cards, setCards] = useState<Card[]>([]);
  const [pendingUid, setPendingUid] = useState<string | null>(null);
  const [manualUid, setManualUid] = useState("");
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

  const onPickCharacter = async (cid: CharacterId) => {
    if (!user || user.character_id === cid) return;
    await updateUser(id, { character_id: cid });
    await load();
  };

  if (!user) {
    return (
      <p className="text-muted" style={{ fontSize: 13 }}>
        로딩...
      </p>
    );
  }

  return (
    <div>
      <div className="toolbar">
        <Link href="/users" className="btn" style={{ textDecoration: "none" }}>
          ← 뒤로
        </Link>
        <span className="sep" />
        <span style={{ fontSize: 13 }}>
          사용자 / <span style={{ fontWeight: 600 }}>{user.name}</span>
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
        <div className="mascot-stage" style={{ flex: "0 0 auto" }}>
          <Avatar
            characterId={user.character_id}
            seed={user.id}
            scale={6}
          />
        </div>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 8,
            flex: 1,
            minWidth: 200,
          }}
        >
          <div style={{ fontSize: 18, fontWeight: 600 }}>{user.name}</div>
          <div style={{ fontSize: 13 }}>
            역할:{" "}
            <span style={{ fontWeight: 600 }}>
              {user.role === "admin" ? "★ 관리자" : "○ 직원"}
            </span>
          </div>
          <div style={{ fontSize: 13 }}>
            상태:{" "}
            {user.active ? (
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
          <div className="text-muted mono" style={{ fontSize: 12 }}>
            ID: {user.id} · 카드 {cards.length}장
          </div>
        </div>
      </div>

      <div className="group">
        <div className="group-title">캐릭터 선택</div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {CHARACTER_LIST.map((c) => {
            const selected = user.character_id === c.id;
            return (
              <button
                key={c.id}
                type="button"
                className={`btn ${selected ? "btn-primary" : ""}`}
                onClick={() => onPickCharacter(c.id)}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: 4,
                  padding: 6,
                  minWidth: 76,
                }}
              >
                <Avatar characterId={c.id} scale={2} />
                <span style={{ fontSize: 12 }}>{c.label}</span>
              </button>
            );
          })}
        </div>
        <div
          className="text-muted mono"
          style={{ fontSize: 12, marginTop: 8 }}
        >
          character_id: {user.character_id}
        </div>
      </div>

      <div className="group">
        <div className="group-title">카드 등록</div>
        {pendingUid ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <div style={{ fontSize: 13 }}>
              감지된 UID: <code className="mono">{pendingUid}</code>
            </div>
            <div
              style={{
                display: "flex",
                gap: 8,
                flexWrap: "wrap",
                alignItems: "center",
              }}
            >
              <input
                className="input"
                placeholder="라벨 (예: 메인)"
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                style={{ width: 200 }}
              />
              <button
                type="button"
                className="btn btn-primary"
                onClick={onSaveCard}
              >
                저장
              </button>
              <button
                type="button"
                className="btn"
                onClick={() => {
                  setPendingUid(null);
                  setLabel("");
                }}
              >
                취소
              </button>
            </div>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <div
              style={{
                display: "flex",
                gap: 8,
                alignItems: "center",
                flexWrap: "wrap",
              }}
            >
              <input
                className="input mono"
                placeholder="UID 직접 입력 (04A1B2C3)"
                value={manualUid}
                onChange={(e) => setManualUid(e.target.value)}
                style={{ width: 220 }}
              />
              <button
                type="button"
                className="btn"
                disabled={!manualUid.trim()}
                onClick={() => {
                  setPendingUid(manualUid.trim().toUpperCase());
                  setManualUid("");
                }}
              >
                다음
              </button>
            </div>
            <button
              type="button"
              className="btn"
              onClick={onScan}
              disabled={scanning}
              style={{ alignSelf: "flex-start" }}
            >
              {scanning ? (
                <span>
                  30초 내 카드 태그<span className="blink">_</span>
                </span>
              ) : (
                "📡 등록 리더로 스캔"
              )}
            </button>
          </div>
        )}
        {error && (
          <p
            style={{ fontSize: 13, color: "var(--accent-red)", marginTop: 8 }}
          >
            {error}
          </p>
        )}
      </div>

      <div
        className="win-in"
        style={{ padding: 2, marginTop: 12, overflowX: "auto" }}
      >
        <table className="pixel-table">
          <thead>
            <tr>
              <th>UID</th>
              <th className="hide-mobile">라벨</th>
              <th className="hide-mobile">등록일</th>
              <th>활성</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {cards.map((c) => (
              <tr key={c.id}>
                <td className="mono">{c.uid}</td>
                <td className="hide-mobile">{c.label ?? "—"}</td>
                <td className="hide-mobile mono" style={{ fontSize: 12 }}>
                  {fmtDate(c.registered_at)}
                </td>
                <td>
                  {c.active ? (
                    <span className="badge badge-ok">
                      <span className="dot" />
                      활성
                    </span>
                  ) : (
                    <span className="badge badge-off">
                      <span className="dot" />
                      분실
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
                    onClick={() => onToggleCard(c)}
                  >
                    {c.active ? "분실 처리" : "재활성"}
                  </button>
                </td>
              </tr>
            ))}
            {cards.length === 0 && (
              <tr>
                <td
                  colSpan={5}
                  style={{
                    padding: "32px 12px",
                    textAlign: "center",
                    color: "var(--win-bg-darker)",
                  }}
                >
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
