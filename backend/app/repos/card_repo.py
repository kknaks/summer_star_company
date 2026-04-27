"""Card 엔티티 DB 접근. 스키마는 docs/spec/database#cards."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Card


async def get_by_id(session: AsyncSession, card_id: UUID) -> Card | None:
    return await session.get(Card, card_id)


async def find_active_by_uid(session: AsyncSession, uid: str) -> Card | None:
    """UID(정규화된)로 활성 카드 1장 조회. 출입 판정용."""
    return await session.scalar(select(Card).where(Card.uid == uid, Card.active.is_(True)))


async def list_all(session: AsyncSession, user_id: UUID | None = None) -> list[Card]:
    stmt = select(Card)
    if user_id is not None:
        stmt = stmt.where(Card.user_id == user_id)
    stmt = stmt.order_by(Card.registered_at.desc())
    result = await session.scalars(stmt)
    return list(result.all())


async def add(
    session: AsyncSession,
    uid: str,
    user_id: UUID,
    label: str | None,
) -> Card:
    """UID는 정규화된 상태로 들어와야 함 (호출자 책임)."""
    card = Card(uid=uid, user_id=user_id, label=label)
    session.add(card)
    await session.flush()
    await session.refresh(card)
    return card


async def update(
    session: AsyncSession,
    card_id: UUID,
    label: str | None = None,
    active: bool | None = None,
) -> Card | None:
    card = await session.get(Card, card_id)
    if card is None:
        return None
    if label is not None:
        card.label = label
    if active is not None:
        card.active = active
    await session.flush()
    await session.refresh(card)
    return card
