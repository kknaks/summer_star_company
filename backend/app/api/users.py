"""User CRUD 라우터. JWT 보호."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentUser, SessionDep
from app.core.exceptions import UserNotFoundError
from app.schemas.users import UserCreate, UserListItemResponse, UserResponse, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[UserListItemResponse])
async def list_users(session: SessionDep, _: CurrentUser) -> list[UserListItemResponse]:
    items = await user_service.list_users(session)
    return [
        UserListItemResponse(
            **UserResponse.model_validate(item.user).model_dump(),
            card_count=item.card_count,
            last_access_at=item.last_access_at,
        )
        for item in items
    ]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, session: SessionDep, _: CurrentUser) -> UserResponse:
    user = await user_service.create_user(session, payload.name)
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    session: SessionDep,
    _: CurrentUser,
) -> UserResponse:
    try:
        user = await user_service.update_user(
            session, user_id, name=payload.name, active=payload.active
        )
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자 없음") from None
    return UserResponse.model_validate(user)
