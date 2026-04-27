"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { dailyStats, monthlyStats } from "@/lib/api/stats";
import { listUsers } from "@/lib/api/users";
import type { DailyStat, MonthlyStat, UserListItem } from "@/lib/types";

export default function StatsPage() {
  const [users, setUsers] = useState<UserListItem[]>([]);
  const [userId, setUserId] = useState<string>("");
  const [view, setView] = useState<"daily" | "monthly">("daily");
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [daily, setDaily] = useState<DailyStat[]>([]);
  const [monthly, setMonthly] = useState<MonthlyStat[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    listUsers().then((us) => {
      setUsers(us);
      if (us.length > 0 && !userId) setUserId(us[0].id);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!userId) return;
    setLoading(true);
    if (view === "daily") {
      dailyStats(userId, year, month).then(setDaily).finally(() => setLoading(false));
    } else {
      monthlyStats(userId, year).then(setMonthly).finally(() => setLoading(false));
    }
  }, [userId, view, year, month]);

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">출퇴근 통계</h2>
      <p className="text-xs text-neutral-500">
        하루 컷오프: KST 04:00 (밤샘 시 다음날 새벽까지 같은 날로 계산)
      </p>

      <div className="flex flex-wrap gap-2 items-center">
        <select
          className="border rounded px-2 py-1 text-sm bg-white"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
        >
          {users.map((u) => (
            <option key={u.id} value={u.id}>
              {u.name}
            </option>
          ))}
        </select>
        <Button
          variant={view === "daily" ? "default" : "outline"}
          size="sm"
          onClick={() => setView("daily")}
        >
          일별
        </Button>
        <Button
          variant={view === "monthly" ? "default" : "outline"}
          size="sm"
          onClick={() => setView("monthly")}
        >
          월별
        </Button>
        <input
          type="number"
          className="border rounded px-2 py-1 text-sm bg-white w-24"
          value={year}
          onChange={(e) => setYear(Number(e.target.value))}
        />
        {view === "daily" && (
          <input
            type="number"
            className="border rounded px-2 py-1 text-sm bg-white w-20"
            min={1}
            max={12}
            value={month}
            onChange={(e) => setMonth(Number(e.target.value))}
          />
        )}
      </div>

      <div className="bg-white border rounded-lg overflow-hidden">
        {view === "daily" ? (
          <table className="w-full text-sm">
            <thead className="bg-neutral-50 text-left">
              <tr>
                <th className="px-3 py-2">일자</th>
                <th className="px-3 py-2">출근</th>
                <th className="px-3 py-2">퇴근</th>
                <th className="px-3 py-2">체류 (분)</th>
              </tr>
            </thead>
            <tbody>
              {daily.map((d) => (
                <tr key={d.date} className="border-t">
                  <td className="px-3 py-2 font-mono">{d.date}</td>
                  <td className="px-3 py-2 font-mono">{d.first_in}</td>
                  <td className="px-3 py-2 font-mono">{d.last_out}</td>
                  <td className="px-3 py-2 font-mono">{d.duration_minutes}</td>
                </tr>
              ))}
              {!loading && daily.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-3 py-8 text-center text-neutral-500">
                    데이터 없음
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-neutral-50 text-left">
              <tr>
                <th className="px-3 py-2">월</th>
                <th className="px-3 py-2">출근일</th>
                <th className="px-3 py-2">평균 출근</th>
                <th className="px-3 py-2">평균 퇴근</th>
                <th className="px-3 py-2">평균 체류 (분)</th>
              </tr>
            </thead>
            <tbody>
              {monthly.map((m) => (
                <tr key={m.month} className="border-t">
                  <td className="px-3 py-2 font-mono">{m.month}</td>
                  <td className="px-3 py-2 font-mono">{m.work_days}</td>
                  <td className="px-3 py-2 font-mono">{m.avg_first_in}</td>
                  <td className="px-3 py-2 font-mono">{m.avg_last_out}</td>
                  <td className="px-3 py-2 font-mono">{m.avg_duration_minutes}</td>
                </tr>
              ))}
              {!loading && monthly.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-3 py-8 text-center text-neutral-500">
                    데이터 없음
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
