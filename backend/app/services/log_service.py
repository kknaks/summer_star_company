"""출입 로그 조회/수동 CRUD 서비스.

비즈니스 룰 SSOT:
- docs/domain/access-log#수동-입력-admin-crud
- docs/spec/backend-api#logs
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AccessLogImmutableFieldError,
    AccessLogNotFoundError,
    FutureOccurredAtError,
    UserNotFoundError,
)
from app.db.models import AccessLog, AccessLogSource
from app.dtos.access import CursorParts, encode_cursor
from app.repos import access_log_repo, user_repo

DEFAULT_LIMIT = 50
MAX_LIMIT = 200


async def list_logs(
    session: AsyncSession,
    *,
    user_id: UUID | None = None,
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
    allowed: bool | None = None,
    include_voided: bool = False,
    cursor: CursorParts | None = None,
    limit: int = DEFAULT_LIMIT,
) -> tuple[list[AccessLog], str | None]:
    """반환: (items, next_cursor). next_cursor None이면 끝."""
    limit = max(1, min(limit, MAX_LIMIT))
    rows = await access_log_repo.list_paginated(
        session,
        user_id=user_id,
        from_dt=from_dt,
        to_dt=to_dt,
        allowed=allowed,
        include_voided=include_voided,
        cursor=cursor,
        limit=limit,
    )
    next_cursor: str | None = None
    if len(rows) > limit:
        last_in_page = rows[limit - 1]
        next_cursor = encode_cursor(last_in_page.occurred_at, last_in_page.id)
        rows = rows[:limit]
    return rows, next_cursor


async def insert_manual(
    session: AsyncSession,
    *,
    user_id: UUID,
    occurred_at: datetime,
    note: str | None,
    actor_id: UUID,
) -> AccessLog:
    """admin 이 누락 탭을 사후 보정. 자동 채움: source='manual', allowed=true, uid=NULL."""
    if occurred_at > datetime.now(UTC):
        raise FutureOccurredAtError("occurred_at 은 미래 시각일 수 없음")
    user = await user_repo.get_by_id(session, user_id)
    if user is None:
        raise UserNotFoundError(f"user_id={user_id}")
    log = await access_log_repo.insert_manual(
        session,
        user_id=user_id,
        occurred_at=occurred_at,
        created_by_user_id=actor_id,
        note=note,
    )
    await session.commit()
    return log


async def update_log(
    session: AsyncSession,
    *,
    log_id: int,
    occurred_at: datetime | None,
    note_provided: bool,
    note: str | None,
    voided: bool | None,
) -> AccessLog:
    """source 별 가능 필드 검증.

    - card: voided / note 만 변경 가능. occurred_at 시도 → 422.
    - manual: occurred_at / note / voided 모두 변경 가능. 미래 시각 거부.
    """
    log = await access_log_repo.get_by_id(session, log_id)
    if log is None:
        raise AccessLogNotFoundError(f"log_id={log_id}")

    updates: dict = {}
    if log.source == AccessLogSource.card and occurred_at is not None:
        raise AccessLogImmutableFieldError(
            "카드 탭(source='card')의 occurred_at 은 수정할 수 없음"
        )
    if occurred_at is not None:
        if occurred_at > datetime.now(UTC):
            raise FutureOccurredAtError("occurred_at 은 미래 시각일 수 없음")
        updates["occurred_at"] = occurred_at
    if note_provided:
        updates["note"] = note
    if voided is not None:
        updates["voided"] = voided

    if not updates:
        return log
    return await _commit_updates(session, log, updates)


async def void_log(session: AsyncSession, *, log_id: int) -> AccessLog:
    """편의 별칭 — DELETE = voided=true. card/manual 모두 가능."""
    log = await access_log_repo.get_by_id(session, log_id)
    if log is None:
        raise AccessLogNotFoundError(f"log_id={log_id}")
    if log.voided:
        return log
    return await _commit_updates(session, log, {"voided": True})


async def _commit_updates(
    session: AsyncSession, log: AccessLog, updates: dict
) -> AccessLog:
    log = await access_log_repo.apply_updates(session, log, updates)
    await session.commit()
    return log
