"""AccessLog DB 접근. 스키마는 docs/spec/database#access_logs."""

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AccessLog


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
