"""Card CRUD 라우터. JWT 보호. /scan은 Phase 4."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentUser, SessionDep
from app.core.exceptions import (
    CardNotFoundError,
    CardScanTimeoutError,
    CardUidConflictError,
    ReaderUnavailableError,
    UserNotFoundError,
)
from app.core.uid import InvalidUidError
from app.schemas.cards import CardCreate, CardResponse, CardScanResponse, CardUpdate
from app.services import card_reader, card_service

router = APIRouter(prefix="/api/cards", tags=["cards"])


@router.post("/scan", response_model=CardScanResponse)
async def scan_card(_: CurrentUser) -> CardScanResponse:
    """등록 리더(#2)에서 카드 한 장 읽어 UID 반환. DB 쓰기 X.

    timeout 내 카드 안 찍히면 408. 리더 불가 시 503.
    """
    try:
        uid = await card_reader.scan_card_uid()
    except CardScanTimeoutError:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="시간 내 카드가 인식되지 않음",
        ) from None
    except ReaderUnavailableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        ) from None
    return CardScanResponse(uid=uid)


@router.get("", response_model=list[CardResponse])
async def list_cards(
    session: SessionDep,
    _: CurrentUser,
    user_id: UUID | None = None,
) -> list[CardResponse]:
    cards = await card_service.list_cards(session, user_id=user_id)
    return [CardResponse.model_validate(c) for c in cards]


@router.post("", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
async def create_card(payload: CardCreate, session: SessionDep, _: CurrentUser) -> CardResponse:
    try:
        card = await card_service.create_card(
            session,
            raw_uid=payload.uid,
            user_id=payload.user_id,
            label=payload.label,
        )
    except InvalidUidError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from None
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자 없음") from None
    except CardUidConflictError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="이미 등록된 UID"
        ) from None
    return CardResponse.model_validate(card)


@router.patch("/{card_id}", response_model=CardResponse)
async def update_card(
    card_id: UUID,
    payload: CardUpdate,
    session: SessionDep,
    _: CurrentUser,
) -> CardResponse:
    try:
        card = await card_service.update_card(
            session, card_id, label=payload.label, active=payload.active
        )
    except CardNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="카드 없음") from None
    return CardResponse.model_validate(card)
