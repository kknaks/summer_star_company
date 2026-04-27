"""출입 로그 조회 서비스. cursor 페이지네이션."""

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AccessLog
from app.dtos.access import CursorParts, encode_cursor
from app.repos import access_log_repo

DEFAULT_LIMIT = 50
MAX_LIMIT = 200


async def list_logs(
    session: AsyncSession,
    *,
    user_id: UUID | None = None,
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
    allowed: bool | None = None,
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
        cursor=cursor,
        limit=limit,
    )
    next_cursor: str | None = None
    if len(rows) > limit:
        last_in_page = rows[limit - 1]
        next_cursor = encode_cursor(last_in_page.occurred_at, last_in_page.id)
        rows = rows[:limit]
    return rows, next_cursor
