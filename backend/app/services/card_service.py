"""Card 비즈니스 로직. UID 정규화 + UNIQUE 충돌 처리."""

from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CardNotFoundError, CardUidConflictError, UserNotFoundError
from app.core.uid import normalize_uid
from app.db.models import Card
from app.repos import card_repo, user_repo


async def list_cards(session: AsyncSession, user_id: UUID | None = None) -> list[Card]:
    return await card_repo.list_all(session, user_id=user_id)


async def create_card(
    session: AsyncSession,
    raw_uid: str,
    user_id: UUID,
    label: str | None,
) -> Card:
    uid = normalize_uid(raw_uid)  # core/uid에서 검증 + 정규화

    user = await user_repo.get_by_id(session, user_id)
    if user is None:
        raise UserNotFoundError(str(user_id))

    try:
        card = await card_repo.add(session, uid=uid, user_id=user_id, label=label)
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise CardUidConflictError(uid) from e
    return card


async def update_card(
    session: AsyncSession,
    card_id: UUID,
    label: str | None = None,
    active: bool | None = None,
) -> Card:
    card = await card_repo.update(session, card_id, label=label, active=active)
    if card is None:
        raise CardNotFoundError(str(card_id))
    await session.commit()
    return card
