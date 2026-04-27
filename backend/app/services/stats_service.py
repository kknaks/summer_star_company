"""출퇴근 통계 서비스. KST 04:00 컷오프 (docs/domain/access-log#출퇴근-해석)."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.repos import access_log_repo

KST = ZoneInfo("Asia/Seoul")


@dataclass
class DailyStat:
    date: str  # "YYYY-MM-DD"
    first_in: str  # "HH:MM" KST
    last_out: str  # "HH:MM" KST
    duration_minutes: int


@dataclass
class MonthlyStat:
    month: str  # "YYYY-MM"
    work_days: int
    avg_first_in: str  # "HH:MM"
    avg_last_out: str
    avg_duration_minutes: int


def _hours_to_hhmm(hours: float) -> str:
    """소수 시간 → HH:MM."""
    total_min = int(round(hours * 60))
    h, m = divmod(total_min, 60)
    return f"{h:02d}:{m:02d}"


def _month_bounds_utc(year: int, month: int) -> tuple[datetime, datetime]:
    """KST 04:00 기준 해당 월의 시작/끝을 UTC로 반환."""
    start_kst = datetime(year, month, 1, 4, 0, tzinfo=KST)
    if month == 12:
        end_kst = datetime(year + 1, 1, 1, 4, 0, tzinfo=KST)
    else:
        end_kst = datetime(year, month + 1, 1, 4, 0, tzinfo=KST)
    return start_kst.astimezone(UTC), end_kst.astimezone(UTC)


def _year_bounds_utc(year: int) -> tuple[datetime, datetime]:
    start_utc = datetime(year, 1, 1, 4, 0, tzinfo=KST).astimezone(UTC)
    end_utc = datetime(year + 1, 1, 1, 4, 0, tzinfo=KST).astimezone(UTC)
    return start_utc, end_utc


async def daily_stats_for_month(
    session: AsyncSession, user_id: UUID, year: int, month: int
) -> list[DailyStat]:
    start_utc, end_utc = _month_bounds_utc(year, month)
    rows = await access_log_repo.daily_stats(
        session, user_id=user_id, start_utc=start_utc, end_utc=end_utc
    )
    items: list[DailyStat] = []
    for day, first_utc, last_utc, dur_min in rows:
        first_kst = first_utc.astimezone(KST)
        last_kst = last_utc.astimezone(KST)
        items.append(
            DailyStat(
                date=day.isoformat() if hasattr(day, "isoformat") else str(day),
                first_in=first_kst.strftime("%H:%M"),
                last_out=last_kst.strftime("%H:%M"),
                duration_minutes=int(dur_min or 0),
            )
        )
    return items


async def monthly_stats_for_year(
    session: AsyncSession, user_id: UUID, year: int
) -> list[MonthlyStat]:
    start_utc, end_utc = _year_bounds_utc(year)
    rows = await access_log_repo.monthly_stats(
        session, user_id=user_id, start_utc=start_utc, end_utc=end_utc
    )
    items: list[MonthlyStat] = []
    for month_str, work_days, avg_first_h, avg_last_h, avg_dur_min in rows:
        items.append(
            MonthlyStat(
                month=month_str,
                work_days=int(work_days),
                avg_first_in=_hours_to_hhmm(float(avg_first_h or 0)),
                avg_last_out=_hours_to_hhmm(float(avg_last_h or 0)),
                avg_duration_minutes=int(avg_dur_min or 0),
            )
        )
    return items


def now_utc() -> datetime:
    """현재 UTC. 디폴트 from/to 계산에 사용."""
    return datetime.now(UTC)


def default_log_window() -> tuple[datetime, datetime]:
    """로그 기본 조회 창 — 최근 30일."""
    end = now_utc()
    return end - timedelta(days=30), end
