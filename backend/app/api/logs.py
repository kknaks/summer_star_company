"""출입 로그 라우터. cursor 페이지네이션 + 필터."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import CurrentUser, SessionDep
from app.dtos.access import decode_cursor
from app.schemas.logs import AccessLogListResponse, AccessLogResponse
from app.services import log_service

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("", response_model=AccessLogListResponse)
async def list_logs(
    session: SessionDep,
    _: CurrentUser,
    user_id: UUID | None = None,
    from_dt: Annotated[datetime | None, Query(alias="from")] = None,
    to_dt: Annotated[datetime | None, Query(alias="to")] = None,
    allowed: bool | None = None,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> AccessLogListResponse:
    cursor_parts = None
    if cursor:
        try:
            cursor_parts = decode_cursor(cursor)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"잘못된 cursor: {e}",
            ) from None

    items, next_cursor = await log_service.list_logs(
        session,
        user_id=user_id,
        from_dt=from_dt,
        to_dt=to_dt,
        allowed=allowed,
        cursor=cursor_parts,
        limit=limit,
    )
    return AccessLogListResponse(
        items=[AccessLogResponse.model_validate(r) for r in items],
        next_cursor=next_cursor,
    )
