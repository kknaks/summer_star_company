"""User 엔티티 DB 접근. 스키마는 docs/spec/database#users."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AccessLog, Card, User, UserRole
from app.dtos.users import UserListItem


async def find_active_admin(session: AsyncSession) -> User | None:
    """1인 운영 — 활성 admin 1명 반환."""
    return await session.scalar(
        select(User).where(User.role == UserRole.admin, User.active.is_(True))
    )


async def get_by_id(session: AsyncSession, user_id: UUID) -> User | None:
    return await session.get(User, user_id)


async def list_with_aggregates(session: AsyncSession) -> list[UserListItem]:
    """전체 사용자 + card_count + last_access_at JOIN."""
    card_count_sub = (
        select(Card.user_id, func.count(Card.id).label("cnt")).group_by(Card.user_id).subquery()
    )
    last_access_sub = (
        select(AccessLog.user_id, func.max(AccessLog.occurred_at).label("last_at"))
        .where(AccessLog.user_id.is_not(None))
        .group_by(AccessLog.user_id)
        .subquery()
    )
    stmt = (
        select(
            User,
            func.coalesce(card_count_sub.c.cnt, 0).label("card_count"),
            last_access_sub.c.last_at.label("last_access_at"),
        )
        .outerjoin(card_count_sub, card_count_sub.c.user_id == User.id)
        .outerjoin(last_access_sub, last_access_sub.c.user_id == User.id)
        .order_by(User.created_at.desc())
    )
    result = await session.execute(stmt)
    return [
        UserListItem(user=row[0], card_count=row[1], last_access_at=row[2]) for row in result.all()
    ]


async def add(session: AsyncSession, name: str) -> User:
    """역할은 자동 admin (현재 enum 값이 admin뿐)."""
    user = User(name=name, role=UserRole.admin)
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user


async def update(
    session: AsyncSession,
    user_id: UUID,
    name: str | None = None,
    active: bool | None = None,
) -> User | None:
    user = await session.get(User, user_id)
    if user is None:
        return None
    if name is not None:
        user.name = name
    if active is not None:
        user.active = active
    await session.flush()
    await session.refresh(user)
    return user
