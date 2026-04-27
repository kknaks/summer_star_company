"""AccessLog DB 접근. 스키마는 docs/spec/database#access_logs."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AccessLog
from app.dtos.access import CursorParts


async def add(
    session: AsyncSession,
    *,
    uid: str,
    occurred_at: datetime,
    allowed: bool,
    card_id: UUID | None = None,
    user_id: UUID | None = None,
) -> AccessLog:
    """received_at은 DB 기본값(NOW())으로 자동."""
    log = AccessLog(
        uid=uid,
        occurred_at=occurred_at,
        allowed=allowed,
        card_id=card_id,
        user_id=user_id,
    )
    session.add(log)
    await session.flush()
    await session.refresh(log)
    return log


async def list_paginated(
    session: AsyncSession,
    *,
    user_id: UUID | None = None,
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
    allowed: bool | None = None,
    cursor: CursorParts | None = None,
    limit: int = 50,
) -> list[AccessLog]:
    """occurred_at DESC, id DESC 정렬. limit + 1까지 가져와 next_cursor 판단은 호출자."""
    stmt = select(AccessLog)

    if user_id is not None:
        stmt = stmt.where(AccessLog.user_id == user_id)
    if from_dt is not None:
        stmt = stmt.where(AccessLog.occurred_at >= from_dt)
    if to_dt is not None:
        stmt = stmt.where(AccessLog.occurred_at < to_dt)
    if allowed is not None:
        stmt = stmt.where(AccessLog.allowed.is_(allowed))

    if cursor is not None:
        stmt = stmt.where(
            or_(
                AccessLog.occurred_at < cursor.occurred_at,
                and_(
                    AccessLog.occurred_at == cursor.occurred_at,
                    AccessLog.id < cursor.log_id,
                ),
            )
        )

    stmt = stmt.order_by(AccessLog.occurred_at.desc(), AccessLog.id.desc()).limit(limit + 1)

    result = await session.scalars(stmt)
    return list(result.all())


# KST 04:00 컷오프 SSOT — docs/domain/access-log#출퇴근-해석
_DAY_BUCKET_SQL = (
    "(date_trunc('day', (occurred_at AT TIME ZONE 'Asia/Seoul') - INTERVAL '4 hours'))::date"
)


async def daily_stats(
    session: AsyncSession,
    *,
    user_id: UUID,
    start_utc: datetime,
    end_utc: datetime,
) -> list[tuple]:
    """일별 출퇴근. 반환: [(day, first_in_utc, last_out_utc, duration_min), ...]"""
    sql = text(f"""
        SELECT
          {_DAY_BUCKET_SQL} AS day,
          MIN(occurred_at) AS first_in_utc,
          MAX(occurred_at) AS last_out_utc,
          EXTRACT(EPOCH FROM (MAX(occurred_at) - MIN(occurred_at))) / 60.0 AS duration_min
        FROM access_logs
        WHERE allowed = TRUE
          AND user_id = :uid
          AND occurred_at >= :start_utc
          AND occurred_at < :end_utc
        GROUP BY day
        ORDER BY day
    """)
    result = await session.execute(
        sql, {"uid": user_id, "start_utc": start_utc, "end_utc": end_utc}
    )
    return list(result.all())


async def monthly_stats(
    session: AsyncSession,
    *,
    user_id: UUID,
    start_utc: datetime,
    end_utc: datetime,
) -> list[tuple]:
    """월별 출퇴근 집계. 반환: [(month, work_days, avg_first_h, avg_last_h, avg_dur_min)]"""
    sql = text(f"""
        WITH daily AS (
          SELECT
            {_DAY_BUCKET_SQL} AS day,
            MIN(occurred_at) AS first_in_utc,
            MAX(occurred_at) AS last_out_utc
          FROM access_logs
          WHERE allowed = TRUE
            AND user_id = :uid
            AND occurred_at >= :start_utc
            AND occurred_at < :end_utc
          GROUP BY day
        )
        SELECT
          to_char(date_trunc('month', day), 'YYYY-MM') AS month,
          COUNT(*) AS work_days,
          AVG(EXTRACT(EPOCH FROM ((first_in_utc AT TIME ZONE 'Asia/Seoul')::time))) / 3600.0 AS avg_first_h,
          AVG(EXTRACT(EPOCH FROM ((last_out_utc AT TIME ZONE 'Asia/Seoul')::time))) / 3600.0 AS avg_last_h,
          AVG(EXTRACT(EPOCH FROM (last_out_utc - first_in_utc))) / 60.0 AS avg_duration_min
        FROM daily
        GROUP BY month
        ORDER BY month
    """)
    result = await session.execute(
        sql, {"uid": user_id, "start_utc": start_utc, "end_utc": end_utc}
    )
    return list(result.all())
