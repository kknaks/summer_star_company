"""User 비즈니스 로직."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UserNotFoundError
from app.db.models import User
from app.dtos.users import UserListItem
from app.repos import user_repo


async def list_users(session: AsyncSession) -> list[UserListItem]:
    return await user_repo.list_with_aggregates(session)


async def create_user(session: AsyncSession, name: str) -> User:
    user = await user_repo.add(session, name)
    await session.commit()
    return user


async def update_user(
    session: AsyncSession,
    user_id: UUID,
    name: str | None = None,
    active: bool | None = None,
) -> User:
    user = await user_repo.update(session, user_id, name=name, active=active)
    if user is None:
        raise UserNotFoundError(str(user_id))
    await session.commit()
    return user
