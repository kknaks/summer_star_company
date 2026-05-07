"""Phase 11 앵커 모델 daily_stats / monthly_stats 검증.

각 케이스마다 access_logs 에 fixture 를 INSERT → daily_stats 호출 → 기대값 비교.
세션 단위 트랜잭션 롤백으로 DB 더럽히지 않음.

규칙 SSOT: docs/domain/access-log#출퇴근-해석
"""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import SessionLocal
from app.repos import access_log_repo

KST = ZoneInfo("Asia/Seoul")

TEST_USER_ID = UUID("9d220ffb-d623-48e9-8b40-074112c41645")  # 김여름

# KST → UTC 헬퍼
def kst(y: int, m: int, d: int, h: int, mi: int = 0, s: int = 0) -> datetime:
    return datetime(y, m, d, h, mi, s, tzinfo=KST).astimezone(UTC)


async def insert_taps(session: AsyncSession, taps_kst: list[tuple], *,
                     allowed: bool = True, voided: bool = False,
                     source: str = "card") -> None:
    """taps_kst: [(year, month, day, hour, minute, second?), ...]"""
    for t in taps_kst:
        occ = kst(*t)
        if source == "manual":
            await session.execute(
                text("""
                    INSERT INTO access_logs (occurred_at, user_id, allowed, voided, source, uid)
                    VALUES (:o, :u, :a, :v, 'manual', NULL)
                """),
                {"o": occ, "u": TEST_USER_ID, "a": allowed, "v": voided},
            )
        else:
            await session.execute(
                text("""
                    INSERT INTO access_logs (occurred_at, user_id, allowed, voided, source, uid)
                    VALUES (:o, :u, :a, :v, 'card', 'TEST0001')
                """),
                {"o": occ, "u": TEST_USER_ID, "a": allowed, "v": voided},
            )
    await session.flush()


async def query_daily(session: AsyncSession, year: int, month: int) -> list[tuple]:
    start = datetime(year, month, 1, 4, 0, tzinfo=KST).astimezone(UTC)
    if month == 12:
        end = datetime(year + 1, 1, 1, 4, 0, tzinfo=KST).astimezone(UTC)
    else:
        end = datetime(year, month + 1, 1, 4, 0, tzinfo=KST).astimezone(UTC)
    return await access_log_repo.daily_stats(
        session, user_id=TEST_USER_ID, start_utc=start, end_utc=end,
    )


def fmt_kst(dt: datetime) -> str:
    return dt.astimezone(KST).strftime("%H:%M:%S")


async def case(name: str, taps: list[tuple], expected: dict) -> bool:
    """taps fixture → daily_stats 결과 → 기대값 비교. 트랜잭션 롤백."""
    async with SessionLocal() as session, session.begin():  # 자동 롤백
        await insert_taps(session, taps)

        # 첫 탭의 KST date 기준으로 한 달 조회
        first = taps[0]
        year, month = first[0], first[1]
        rows = await query_daily(session, year, month)

        # raise/rollback 자동
        ok = True
        failures = []

        if len(rows) != expected["row_count"]:
            ok = False
            failures.append(f"row_count: {len(rows)} != {expected['row_count']}")
        elif expected["row_count"] > 0:
            day, first_utc, last_utc, dur_min = rows[0]
            e = expected
            if "first_in" in e and fmt_kst(first_utc)[:5] != e["first_in"]:
                ok = False
                failures.append(f"first_in: {fmt_kst(first_utc)} != {e['first_in']}")
            if "last_out" in e and fmt_kst(last_utc)[:5] != e["last_out"]:
                ok = False
                failures.append(f"last_out: {fmt_kst(last_utc)} != {e['last_out']}")
            if "duration_min" in e and abs(float(dur_min) - e["duration_min"]) > 0.5:
                ok = False
                failures.append(f"duration_min: {dur_min} != {e['duration_min']}")

        mark = "✓" if ok else "✗"
        print(f"{mark} {name}")
        for f in failures:
            print(f"    {f}")
        if rows:
            day, first_utc, last_utc, dur_min = rows[0]
            print(f"    rows[0] = day={day} first={fmt_kst(first_utc)} last={fmt_kst(last_utc)} dur={dur_min}")
        await session.rollback()
        return ok


async def main() -> int:
    results = []

    # 1. 정상 2탭 — [09, 18]
    results.append(await case(
        "정상 2탭 [09, 18]",
        [(2026, 5, 1, 9, 0), (2026, 5, 1, 18, 0)],
        {"row_count": 1, "first_in": "09:00", "last_out": "18:00", "duration_min": 540},
    ))

    # 2. 정상 4탭 페어 휴게 — [09, 12, 13, 18]
    results.append(await case(
        "정상 4탭 [09, 12, 13, 18] (휴게 1h)",
        [(2026, 5, 2, 9, 0), (2026, 5, 2, 12, 0), (2026, 5, 2, 13, 0), (2026, 5, 2, 18, 0)],
        {"row_count": 1, "first_in": "09:00", "last_out": "18:00", "duration_min": 480},
    ))

    # 3. 홀수 3탭 (퇴근 누락) — [09, 12, 13]
    results.append(await case(
        "홀수 3탭 [09, 12, 13] (orphan→퇴근 1h 휴게)",
        [(2026, 5, 3, 9, 0), (2026, 5, 3, 12, 0), (2026, 5, 3, 13, 0)],
        {"row_count": 1, "first_in": "09:00", "last_out": "13:00", "duration_min": 180},
    ))

    # 4. 홀수 5탭 (중간 누락) — [09, 12, 13, 14, 18]
    results.append(await case(
        "홀수 5탭 [09, 12, 13, 14, 18] (페어 1h + orphan 4h)",
        [
            (2026, 5, 4, 9, 0),
            (2026, 5, 4, 12, 0),
            (2026, 5, 4, 13, 0),
            (2026, 5, 4, 14, 0),
            (2026, 5, 4, 18, 0),
        ],
        {"row_count": 1, "first_in": "09:00", "last_out": "18:00", "duration_min": 240},
    ))

    # 5. 1탭 only — [09]
    results.append(await case(
        "1탭 only [09] (duration=0)",
        [(2026, 5, 5, 9, 0)],
        {"row_count": 1, "first_in": "09:00", "last_out": "09:00", "duration_min": 0},
    ))

    # 6. 30초 더블탭 흡수 — [09:00:00, 09:00:15, 18:00]
    results.append(await case(
        "30초 더블탭 [09:00:00, 09:00:15, 18:00] → 1탭으로 흡수",
        [(2026, 5, 6, 9, 0, 0), (2026, 5, 6, 9, 0, 15), (2026, 5, 6, 18, 0)],
        {"row_count": 1, "first_in": "09:00", "last_out": "18:00", "duration_min": 540},
    ))

    # 7. KST 04:00 컷오프 경계 — 03:59 KST는 전날, 04:01 KST는 당일
    # 2026-05-07 03:59 KST 탭은 5/6 day 로 들어가야 함, 2026-05-07 04:01 KST 는 5/7
    async with SessionLocal() as session, session.begin():
        await insert_taps(session, [
            (2026, 5, 7, 3, 59),  # 5/6 day
            (2026, 5, 7, 4, 1),   # 5/7 day (출근)
            (2026, 5, 7, 18, 0),  # 5/7 day (퇴근)
        ])
        rows = await query_daily(session, 2026, 5)
        # 5/6 day 1건 + 5/7 day 1건 = 2 row
        day_5_6 = [r for r in rows if str(r[0]) == "2026-05-06"]
        day_5_7 = [r for r in rows if str(r[0]) == "2026-05-07"]
        ok = True
        if not day_5_6:
            ok = False
            print("✗ 컷오프 경계: 5/6 day 없음")
        elif fmt_kst(day_5_6[0][1])[:5] != "03:59":
            ok = False
            print(f"✗ 컷오프 경계: 5/6 first_in {fmt_kst(day_5_6[0][1])} != 03:59")
        if not day_5_7:
            ok = False
            print("✗ 컷오프 경계: 5/7 day 없음")
        elif fmt_kst(day_5_7[0][1])[:5] != "04:01":
            ok = False
            print(f"✗ 컷오프 경계: 5/7 first_in {fmt_kst(day_5_7[0][1])} != 04:01")
        if ok:
            print("✓ KST 04:00 컷오프 경계 — 03:59 → 전날, 04:01 → 당일")
        results.append(ok)
        await session.rollback()

    # 8. voided 제외 — 4탭 중 휴게 2개 (12,13)을 voided 처리하면 페어 없어짐
    async with SessionLocal() as session, session.begin():
        # 정상 row 2개
        await insert_taps(session, [(2026, 5, 8, 9, 0), (2026, 5, 8, 18, 0)])
        # voided row 2개 (휴게 페어)
        await insert_taps(session, [(2026, 5, 8, 12, 0), (2026, 5, 8, 13, 0)],
                          voided=True)
        rows = await query_daily(session, 2026, 5)
        day = [r for r in rows if str(r[0]) == "2026-05-08"]
        ok = True
        if not day:
            ok = False
        else:
            _, first_utc, last_utc, dur = day[0]
            # voided 제외라 [09, 18] 만 → 9h
            if abs(float(dur) - 540) > 0.5:
                ok = False
                print(f"✗ voided 제외: dur={dur} != 540")
        print(f"{'✓' if ok else '✗'} voided 제외 — 휴게 페어 voided → 9h 그대로")
        results.append(ok)
        await session.rollback()

    print()
    print(f"통과: {sum(results)}/{len(results)}")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
