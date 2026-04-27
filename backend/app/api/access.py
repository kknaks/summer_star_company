"""출입 라우터. Pi 에이전트의 X-Agent-Key 인증 push 엔드포인트.

엔드포인트 SSOT: docs/spec/backend-api#access.
"""

from fastapi import APIRouter, HTTPException, status

from app.core.deps import AgentAuth, SessionDep
from app.core.uid import InvalidUidError
from app.schemas.access import AccessRequest, AccessResponse
from app.services import access_service

router = APIRouter(prefix="/api/access", tags=["access"])


@router.post("", response_model=AccessResponse)
async def record_access(
    payload: AccessRequest, session: SessionDep, _: AgentAuth
) -> AccessResponse:
    try:
        allowed = await access_service.record_access(
            session, raw_uid=payload.uid, occurred_at=payload.occurred_at
        )
    except InvalidUidError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from None
    return AccessResponse(allowed=allowed)
