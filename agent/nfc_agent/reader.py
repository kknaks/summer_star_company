"""출입용 리더(#1) 감시. pyscard CardRequest 블로킹.

UID 정규화 정책: docs/domain/card.md (대문자 hex, 구분자 제거).
backend의 normalize_uid와 의도적 중복 — repo-layout.md 참고.
"""

import logging
import time

from smartcard.CardRequest import CardRequest
from smartcard.CardType import AnyCardType
from smartcard.Exceptions import (
    CardConnectionException,
    CardRequestTimeoutException,
    NoCardException,
)
from smartcard.System import readers

from nfc_agent.config import settings

logger = logging.getLogger(__name__)


class ReaderError(Exception):
    pass


# ACR122U PSEUDO-APDU: GET DATA — UID 조회
_GET_UID_APDU = [0xFF, 0xCA, 0x00, 0x00, 0x00]
# ACR122U 카드 감지 시 부저 끄기 (P2=00)
_DISABLE_BUZZER_APDU = [0xFF, 0x00, 0x52, 0x00, 0x00]
# 60초 단위로 재대기 — SIGINT 등 시그널 처리 지연 최소화
_POLL_TIMEOUT_SEC = 60
# 같은 UID 디바운스 윈도우 — 카드를 리더 위에 계속 올려둔 상태에서 폭주 방지
_DEBOUNCE_SEC = 1.5


def _find_reader():
    available = readers()
    if not available:
        raise ReaderError("연결된 PC/SC 리더 없음")
    for r in available:
        if settings.READER_NAME in str(r):
            return r
    logger.warning(
        "READER_NAME=%r 매칭 실패, 첫 번째 리더 사용: %s",
        settings.READER_NAME,
        available[0],
    )
    return available[0]


def _normalize_uid(raw: str) -> str:
    cleaned = raw.replace(":", "").replace("-", "").replace(" ", "").upper()
    if not cleaned:
        raise ReaderError("UID 비어있음")
    int(cleaned, 16)  # hex 검증
    return cleaned


# 모듈 레벨 디바운스 상태 — 카드 한번 처리 후 같은 UID 즉시 재처리 방지.
# 함수 로컬로 두면 매 wait_for_card 호출마다 리셋되어 의미 없음.
_last_uid: str | None = None
_last_time: float = 0.0


def wait_for_card() -> str:
    """카드 한 장 대기 후 UID(정규화) 반환.

    `newcardonly=True` — 카드가 새로 인서트된 이벤트만 트리거.
    추가로 같은 UID 디바운스 윈도우(_DEBOUNCE_SEC)로 안전장치.
    """
    global _last_uid, _last_time
    target_reader = _find_reader()

    while True:
        try:
            card_service = CardRequest(
                readers=[target_reader],
                timeout=_POLL_TIMEOUT_SEC,
                cardType=AnyCardType(),
                newcardonly=True,
            ).waitforcard()
        except CardRequestTimeoutException:
            continue
        except Exception as e:
            raise ReaderError(f"리더 통신 실패: {e}") from e

        try:
            card_service.connection.connect()
            # 부저 끄기 — 실패해도 본 흐름은 계속
            try:
                card_service.connection.transmit(_DISABLE_BUZZER_APDU)
            except Exception:
                logger.debug("부저 끄기 APDU 실패 (무시)")
            response, sw1, sw2 = card_service.connection.transmit(_GET_UID_APDU)
            if sw1 != 0x90 or sw2 != 0x00:
                raise ReaderError(f"GET_UID APDU 비정상 SW={sw1:02X}{sw2:02X}")
            uid = _normalize_uid(bytes(response).hex())
        except (CardConnectionException, NoCardException):
            time.sleep(0.3)
            continue
        finally:
            try:
                card_service.connection.disconnect()
            except Exception:
                logger.exception("리더 disconnect 실패")

        now = time.monotonic()
        if uid == _last_uid and (now - _last_time) < _DEBOUNCE_SEC:
            time.sleep(0.3)
            continue
        _last_uid = uid
        _last_time = now
        return uid
