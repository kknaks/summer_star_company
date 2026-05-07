"""AccessLog DB 접근. 스키마는 docs/spec/database#access_logs."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AccessLog, AccessLogSource
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
    """카드 탭 INSERT (source='card'). received_at은 DB 기본값(NOW())."""
    log = AccessLog(
        uid=uid,
        occurred_at=occurred_at,
        allowed=allowed,
        card_id=card_id,
        user_id=user_id,
        source=AccessLogSource.card,
    )
    session.add(log)
    await session.flush()
    await session.refresh(log)
    return log


async def insert_manual(
    session: AsyncSession,
    *,
    user_id: UUID,
    occurred_at: datetime,
    created_by_user_id: UUID,
    note: str | None = None,
) -> AccessLog:
    """수동 입력 (source='manual'). uid/card_id NULL, allowed=true 강제. CHECK 제약과 정합."""
    log = AccessLog(
        uid=None,
        occurred_at=occurred_at,
        allowed=True,
        card_id=None,
        user_id=user_id,
        source=AccessLogSource.manual,
        created_by_user_id=created_by_user_id,
        note=note,
    )
    session.add(log)
    await session.flush()
    await session.refresh(log)
    return log


async def get_by_id(session: AsyncSession, log_id: int) -> AccessLog | None:
    return await session.get(AccessLog, log_id)


async def apply_updates(
    session: AsyncSession, log: AccessLog, updates: dict
) -> AccessLog:
    """updates 의 키만 log 에 적용. 호출자(서비스)가 source 별 가능 필드 검증.

    허용 키: occurred_at, note, voided.
    """
    for key, value in updates.items():
        setattr(log, key, value)
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
    include_voided: bool = False,
    cursor: CursorParts | None = None,
    limit: int = 50,
) -> list[AccessLog]:
    """occurred_at DESC, id DESC 정렬. limit + 1까지 가져와 next_cursor 판단은 호출자.

    include_voided=False (기본) 면 voided 행 제외. True면 모두 반환.
    """
    stmt = select(AccessLog)

    if not include_voided:
        stmt = stmt.where(AccessLog.voided.is_(False))
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


# 출퇴근 해석 SSOT — docs/domain/access-log#출퇴근-해석
#
# 앵커 모델:
#   1. KST 04:00 컷오프로 day bucket
#   2. 30초 더블탭 흡수 (인접 탭과 30초 이내면 1건으로)
#   3. 출근 = rn=1, 퇴근 = rn=cnt (앵커 고정)
#   4. 중간 탭 페어링: rn 짝수에서 다음 탭(rn+1)까지가 휴게 1건
#      rn=cnt-1 (즉 마지막 중간 탭이 짝수 = orphan)이면 LEAD가 곧 last_out → 퇴근까지 휴게로 자동 처리
#   5. duration = (last - first) - ∑break, 단 cnt=1이면 0

_DAY_BUCKET_SQL = (
    "(date_trunc('day', (occurred_at AT TIME ZONE 'Asia/Seoul') - INTERVAL '4 hours'))::date"
)

_DAILY_CTES = f"""
    normalized AS (
      SELECT
        occurred_at,
        {_DAY_BUCKET_SQL} AS day
      FROM access_logs
      WHERE NOT voided
        AND allowed = TRUE
        AND user_id = :uid
        AND occurred_at >= :start_utc
        AND occurred_at < :end_utc
    ),
    cluster_marks AS (
      SELECT
        occurred_at,
        day,
        CASE
          WHEN LAG(occurred_at) OVER (PARTITION BY day ORDER BY occurred_at) IS NULL
            OR occurred_at - LAG(occurred_at) OVER (PARTITION BY day ORDER BY occurred_at)
               > INTERVAL '30 seconds'
          THEN 1 ELSE 0
        END AS new_cluster
      FROM normalized
    ),
    clustered AS (
      SELECT
        occurred_at,
        day,
        SUM(new_cluster) OVER (
          PARTITION BY day ORDER BY occurred_at ROWS UNBOUNDED PRECEDING
        ) AS cluster_id
      FROM cluster_marks
    ),
    deduped AS (
      SELECT day, MIN(occurred_at) AS occurred_at
      FROM clustered
      GROUP BY day, cluster_id
    ),
    ranked AS (
      SELECT
        day,
        occurred_at,
        ROW_NUMBER() OVER (PARTITION BY day ORDER BY occurred_at) AS rn,
        COUNT(*)     OVER (PARTITION BY day) AS cnt,
        LEAD(occurred_at) OVER (PARTITION BY day ORDER BY occurred_at) AS next_at
      FROM deduped
    ),
    per_day AS (
      SELECT
        day,
        MIN(occurred_at) AS first_in_utc,
        MAX(occurred_at) AS last_out_utc,
        COALESCE(SUM(
          CASE
            WHEN rn % 2 = 0 AND rn BETWEEN 2 AND cnt - 1
            THEN EXTRACT(EPOCH FROM (next_at - occurred_at)) / 60.0
            ELSE 0
          END
        ), 0) AS break_minutes
      FROM ranked
      GROUP BY day
    )
"""


async def daily_stats(
    session: AsyncSession,
    *,
    user_id: UUID,
    start_utc: datetime,
    end_utc: datetime,
) -> list[tuple]:
    """일별 출퇴근. 반환: [(day, first_in_utc, last_out_utc, duration_min), ...]"""
    sql = text(f"""
        WITH {_DAILY_CTES}
        SELECT
          day,
          first_in_utc,
          last_out_utc,
          GREATEST(
            EXTRACT(EPOCH FROM (last_out_utc - first_in_utc)) / 60.0 - break_minutes,
            0
          ) AS duration_min
        FROM per_day
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
    """월별 출퇴근 집계. 반환: [(month, work_days, avg_first_h, avg_last_h, avg_dur_min)]

    avg_duration 은 일별 duration(휴게 차감 후)을 평균낸 값.
    """
    sql = text(f"""
        WITH {_DAILY_CTES},
        daily AS (
          SELECT
            day,
            first_in_utc,
            last_out_utc,
            GREATEST(
              EXTRACT(EPOCH FROM (last_out_utc - first_in_utc)) / 60.0 - break_minutes,
              0
            ) AS duration_min
          FROM per_day
        )
        SELECT
          to_char(date_trunc('month', day), 'YYYY-MM') AS month,
          COUNT(*) AS work_days,
          AVG(EXTRACT(EPOCH FROM ((first_in_utc AT TIME ZONE 'Asia/Seoul')::time))) / 3600.0 AS avg_first_h,
          AVG(EXTRACT(EPOCH FROM ((last_out_utc AT TIME ZONE 'Asia/Seoul')::time))) / 3600.0 AS avg_last_h,
          AVG(duration_min) AS avg_duration_min
        FROM daily
        GROUP BY month
        ORDER BY month
    """)
    result = await session.execute(
        sql, {"uid": user_id, "start_utc": start_utc, "end_utc": end_utc}
    )
    return list(result.all())
