"""User 엔티티 DB 접근 계층. 스키마는 docs/spec/database#users."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, UserRole


async def find_active_admin(session: AsyncSession) -> User | None:
    """1인 운영 스코프 — 활성 admin 1명을 반환 (없으면 None)."""
    return await session.scalar(
        select(User).where(User.role == UserRole.admin, User.active.is_(True))
    )


async def get_by_id(session: AsyncSession, user_id: UUID) -> User | None:
    return await session.get(User, user_id)
