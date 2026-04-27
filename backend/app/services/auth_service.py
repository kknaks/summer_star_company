"""인증 비즈니스 로직. router와 repo 사이 레이어. schemas import 금지."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, verify_password
from app.db.models import User
from app.repos import user_repo


async def authenticate_admin(session: AsyncSession, password: str) -> User | None:
    admin = await user_repo.find_active_admin(session)
    if admin is None or admin.password_hash is None:
        return None
    if not verify_password(password, admin.password_hash):
        return None
    return admin


def issue_token(user: User) -> str:
    return create_access_token(user.id, user.role.value)
