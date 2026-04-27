"""인증 라우터. 비밀번호 로그인 → JWT 발급, /me 조회.

엔드포인트 SSOT: docs/spec/backend-api#auth.
"""

from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentUser, SessionDep
from app.schemas.auth import LoginRequest, LoginResponse, UserPublic
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, session: SessionDep) -> LoginResponse:
    user = await auth_service.authenticate_admin(session, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="잘못된 비밀번호",
        )
    return LoginResponse(
        token=auth_service.issue_token(user),
        user=UserPublic.model_validate(user),
    )


@router.get("/me", response_model=UserPublic)
async def me(user: CurrentUser) -> UserPublic:
    return UserPublic.model_validate(user)
