"""FastAPI 의존성. 인증/세션 등 router에서 Depends()로 주입."""

from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.base import get_session
from app.db.models import User
from app.repos import user_repo

bearer_scheme = HTTPBearer(auto_error=False)

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    session: SessionDep,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="토큰 누락")
    try:
        payload = decode_access_token(creds.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="토큰 만료") from None
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 토큰"
        ) from None

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="토큰 페이로드 오류")

    user = await user_repo.get_by_id(session, UUID(sub))
    if user is None or not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="사용자 없음 또는 비활성"
        )
    return user


async def verify_agent_key(
    x_agent_key: Annotated[str | None, Header(alias="X-Agent-Key")] = None,
) -> None:
    if x_agent_key != settings.AGENT_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="잘못된 에이전트 키")


CurrentUser = Annotated[User, Depends(get_current_user)]
AgentAuth = Annotated[None, Depends(verify_agent_key)]
