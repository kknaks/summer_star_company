"""출입 판정 서비스. UID 정규화 → 카드/사용자 조회 → 로그 기록."""

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.uid import normalize_uid
from app.repos import access_log_repo, card_repo, user_repo


async def record_access(session: AsyncSession, raw_uid: str, occurred_at: datetime) -> bool:
    """판정 + 로그 기록. allowed 반환.

    InvalidUidError는 호출자(라우터)가 422로 변환하므로 여기선 catch X.
    """
    uid = normalize_uid(raw_uid)

    card = await card_repo.find_active_by_uid(session, uid)
    if card is None:
        # 미등록 또는 비활성 카드 — uid raw로 보존
        await access_log_repo.add(session, uid=uid, occurred_at=occurred_at, allowed=False)
        await session.commit()
        return False

    user = await user_repo.get_by_id(session, card.user_id)
    if user is None or not user.active:
        await access_log_repo.add(
            session,
            uid=uid,
            occurred_at=occurred_at,
            allowed=False,
            card_id=card.id,
            user_id=card.user_id,
        )
        await session.commit()
        return False

    # 정상 — 허용
    await access_log_repo.add(
        session,
        uid=uid,
        occurred_at=occurred_at,
        allowed=True,
        card_id=card.id,
        user_id=user.id,
    )
    await session.commit()
    return True
