"use client";

import { useEffect, useState } from "react";

import Icon from "@/components/pixel/Icon";
import Select from "@/components/win98/Select";
import { dailyStats, monthlyStats } from "@/lib/api/stats";
import { listUsers } from "@/lib/api/users";
import type { DailyStat, MonthlyStat, UserListItem } from "@/lib/types";

function isWeekend(dateStr: string) {
  const [y, m, d] = dateStr.split("-").map(Number);
  const dow = new Date(Date.UTC(y, m - 1, d)).getUTCDay();
  return dow === 0 || dow === 6;
}

function pad2(n: number) {
  return String(n).padStart(2, "0");
}

function buildMonthDays(
  year: number,
  month: number,
  daily: DailyStat[],
): DailyStat[] {
  const daysInMonth = new Date(year, month, 0).getDate();
  const today = new Date();
  const isCurrent =
    year === today.getFullYear() && month === today.getMonth() + 1;
  const isFuture =
    year > today.getFullYear() ||
    (year === today.getFullYear() && month > today.getMonth() + 1);
  const lastDay = isFuture ? 0 : isCurrent ? today.getDate() : daysInMonth;
  const map = new Map(daily.map((d) => [d.date, d]));
  const result: DailyStat[] = [];
  for (let day = 1; day <= lastDay; day += 1) {
    const dateStr = `${year}-${pad2(month)}-${pad2(day)}`;
    result.push(
      map.get(dateStr) ?? {
        date: dateStr,
        first_in: "",
        last_out: "",
        duration_minutes: 0,
      },
    );
  }
  return result;
}

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
      dailyStats(userId, year, month)
        .then(setDaily)
        .finally(() => setLoading(false));
    } else {
      monthlyStats(userId, year)
        .then(setMonthly)
        .finally(() => setLoading(false));
    }
  }, [userId, view, year, month]);

  const dailyAll = buildMonthDays(year, month, daily);
  const maxDur = Math.max(1, ...daily.map((d) => d.duration_minutes));
  const maxMonthDur = Math.max(
    1,
    ...monthly.map((m) => m.avg_duration_minutes),
  );

  const totalMinutes = daily.reduce((a, b) => a + b.duration_minutes, 0);
  const totalMonthDays = monthly.reduce((a, b) => a + b.work_days, 0);
  const avgMonthMinutes = monthly.length
    ? Math.floor(
        monthly.reduce((a, b) => a + b.avg_duration_minutes, 0) /
          monthly.length,
      )
    : 0;

  return (
    <div>
      <div className="toolbar">
        <Select
          value={userId}
          onChange={setUserId}
          options={users.map((u) => ({ value: u.id, label: u.name }))}
          ariaLabel="사용자 선택"
          style={{ minWidth: 140 }}
        />
        <span className="sep" />
        <button
          type="button"
          className={`btn ${view === "daily" ? "active" : ""}`}
          onClick={() => setView("daily")}
        >
          일별
        </button>
        <button
          type="button"
          className={`btn ${view === "monthly" ? "active" : ""}`}
          onClick={() => setView("monthly")}
        >
          월별
        </button>
        <span className="sep" />
        <Select
          value={String(year)}
          onChange={(v) => setYear(Number(v))}
          options={Array.from({ length: 5 }, (_, i) => {
            const y = now.getFullYear() - 2 + i;
            return { value: String(y), label: `${y}년` };
          })}
          ariaLabel="년 선택"
          style={{ minWidth: 100 }}
        />
        {view === "daily" && (
          <Select
            value={String(month)}
            onChange={(v) => setMonth(Number(v))}
            options={Array.from({ length: 12 }, (_, i) => ({
              value: String(i + 1),
              label: `${i + 1}월`,
            }))}
            ariaLabel="월 선택"
            style={{ minWidth: 80 }}
          />
        )}
      </div>

      <div
        className="text-muted"
        style={{ fontSize: 12, marginTop: 4, padding: 8 }}
      >
        ※ 하루 컷오프: KST 04:00 (밤샘 시 다음날 새벽까지 같은 날로 계산)
      </div>

      <div
        style={{
          display: "flex",
          gap: 12,
          flexWrap: "wrap",
          marginTop: 8,
        }}
      >
        {view === "daily" ? (
          <>
            <div className="stat-tile" style={{ flex: "1 1 180px" }}>
              <div className="ico">
                <Icon name="log" scale={2} />
              </div>
              <div>
                <div className="num">
                  {daily.length}
                  <span style={{ fontSize: 14 }}>일</span>
                </div>
                <div className="lbl">출근일</div>
              </div>
            </div>
            <div className="stat-tile" style={{ flex: "1 1 180px" }}>
              <div className="ico">
                <Icon name="clock" scale={2} />
              </div>
              <div>
                <div className="num">
                  {Math.floor(totalMinutes / 60)}
                  <span style={{ fontSize: 14 }}>h</span>
                </div>
                <div className="lbl">총 체류</div>
              </div>
            </div>
            <div className="stat-tile" style={{ flex: "1 1 180px" }}>
              <div className="ico">
                <Icon name="star" scale={2} />
              </div>
              <div>
                <div className="num mono">{daily[0]?.first_in ?? "—"}</div>
                <div className="lbl">최근 출근</div>
              </div>
            </div>
          </>
        ) : (
          <>
            <div className="stat-tile" style={{ flex: "1 1 180px" }}>
              <div className="ico">
                <Icon name="chart" scale={2} />
              </div>
              <div>
                <div className="num">
                  {totalMonthDays}
                  <span style={{ fontSize: 14 }}>일</span>
                </div>
                <div className="lbl">올해 출근일</div>
              </div>
            </div>
            <div className="stat-tile" style={{ flex: "1 1 180px" }}>
              <div className="ico">
                <Icon name="clock" scale={2} />
              </div>
              <div>
                <div className="num mono">
                  {Math.floor(avgMonthMinutes / 60)}h{avgMonthMinutes % 60}m
                </div>
                <div className="lbl">평균 체류</div>
              </div>
            </div>
          </>
        )}
      </div>

      <div className="group">
        <div className="group-title">
          픽셀 차트 —{" "}
          {view === "daily"
            ? `${year}.${month} 일별 체류 분`
            : `${year} 월별 평균 체류 분`}
        </div>
        <div className="bar-chart">
          {view === "daily"
            ? dailyAll.map((d) => {
                const empty = d.duration_minutes === 0;
                const blocks = empty
                  ? 0
                  : Math.max(1, Math.round((d.duration_minutes / maxDur) * 16));
                const weekend = isWeekend(d.date);
                return (
                  <div className="bar" key={d.date}>
                    {!empty && (
                      <div className="value">{d.duration_minutes}</div>
                    )}
                    <div className="blocks" style={{ height: "85%" }}>
                      {empty ? (
                        <div className="block empty" />
                      ) : (
                        Array.from({ length: blocks }).map((_, i) => (
                          <div
                            key={i}
                            className={`block ${weekend ? "weekend" : ""}`}
                          />
                        ))
                      )}
                    </div>
                    <div className="label">{Number(d.date.slice(-2))}</div>
                  </div>
                );
              })
            : monthly.map((m) => {
                const blocks = Math.max(
                  1,
                  Math.round((m.avg_duration_minutes / maxMonthDur) * 16),
                );
                return (
                  <div className="bar" key={m.month}>
                    <div className="value">{m.avg_duration_minutes}</div>
                    <div className="blocks" style={{ height: "85%" }}>
                      {Array.from({ length: blocks }).map((_, i) => (
                        <div key={i} className="block" />
                      ))}
                    </div>
                    <div className="label">
                      {Number(m.month.slice(-2))}월
                    </div>
                  </div>
                );
              })}
        </div>
      </div>

      <div
        className="win-in"
        style={{ padding: 2, marginTop: 12, overflowX: "auto" }}
      >
        {view === "daily" ? (
          <table className="pixel-table">
            <thead>
              <tr>
                <th>일자</th>
                <th>출근</th>
                <th>퇴근</th>
                <th>체류 (분)</th>
              </tr>
            </thead>
            <tbody>
              {daily.map((d) => (
                <tr key={d.date}>
                  <td className="mono">
                    {d.date}
                    {isWeekend(d.date) && (
                      <span
                        className="text-muted"
                        style={{ fontSize: 12, marginLeft: 4 }}
                      >
                        (주말)
                      </span>
                    )}
                  </td>
                  <td className="mono">{d.first_in}</td>
                  <td className="mono">{d.last_out}</td>
                  <td className="mono">{d.duration_minutes}</td>
                </tr>
              ))}
              {!loading && daily.length === 0 && (
                <tr>
                  <td
                    colSpan={4}
                    style={{
                      padding: "32px 12px",
                      textAlign: "center",
                      color: "var(--win-bg-darker)",
                    }}
                  >
                    데이터 없음
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        ) : (
          <table className="pixel-table">
            <thead>
              <tr>
                <th>월</th>
                <th>출근일</th>
                <th className="hide-mobile">평균 출근</th>
                <th className="hide-mobile">평균 퇴근</th>
                <th>평균 체류</th>
              </tr>
            </thead>
            <tbody>
              {monthly.map((m) => (
                <tr key={m.month}>
                  <td className="mono">{m.month}</td>
                  <td className="mono">{m.work_days}</td>
                  <td className="mono hide-mobile">{m.avg_first_in}</td>
                  <td className="mono hide-mobile">{m.avg_last_out}</td>
                  <td className="mono">{m.avg_duration_minutes}분</td>
                </tr>
              ))}
              {!loading && monthly.length === 0 && (
                <tr>
                  <td
                    colSpan={5}
                    style={{
                      padding: "32px 12px",
                      textAlign: "center",
                      color: "var(--win-bg-darker)",
                    }}
                  >
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
