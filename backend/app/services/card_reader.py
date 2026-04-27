"""등록용 리더(#2) 제어. pyscard로 PC/SC 직접 통신.

도메인 흐름은 docs/domain/card.md#등록-흐름.
운영 메모는 docs/spec/backend-api.md#등록-리더2-운영.
"""

import asyncio
import logging

from smartcard.CardRequest import CardRequest
from smartcard.CardType import AnyCardType
from smartcard.Exceptions import (
    CardConnectionException,
    CardRequestTimeoutException,
    NoCardException,
)
from smartcard.System import readers

from app.core.config import settings
from app.core.exceptions import CardScanTimeoutError, ReaderUnavailableError
from app.core.uid import normalize_uid

logger = logging.getLogger(__name__)

# ACR122U PSEUDO-APDU: GET DATA — UID 조회 (ISO14443-3 type A/B 공통)
_GET_UID_APDU = [0xFF, 0xCA, 0x00, 0x00, 0x00]
# one-shot 비프: 카드 읽기 성공 시 능동 트리거
_BEEP_APDU = [0xFF, 0x00, 0x40, 0x00, 0x04, 0x01, 0x00, 0x01, 0x01]


def _find_reader(name_filter: str):
    available = readers()
    if not available:
        raise ReaderUnavailableError("연결된 PC/SC 리더 없음")
    for reader in available:
        if name_filter in str(reader):
            return reader
    # filter 불일치 시 첫 번째 리더로 fallback (1대 전제)
    logger.warning("READER_NAME=%r 매칭 실패, 첫 번째 리더 사용: %s", name_filter, available[0])
    return available[0]


def _read_uid_blocking(timeout_sec: int) -> str:
    target_reader = _find_reader(settings.READER_NAME)

    try:
        card_request = CardRequest(
            readers=[target_reader],
            timeout=timeout_sec,
            cardType=AnyCardType(),
        )
        card_service = card_request.waitforcard()
    except CardRequestTimeoutException as e:
        raise CardScanTimeoutError(f"{timeout_sec}초 내 카드 안 찍힘") from e
    except Exception as e:
        raise ReaderUnavailableError(f"리더 통신 실패: {e}") from e

    try:
        card_service.connection.connect()
        response, sw1, sw2 = card_service.connection.transmit(_GET_UID_APDU)
        if sw1 != 0x90 or sw2 != 0x00:
            raise ReaderUnavailableError(f"GET_UID APDU 응답 비정상: SW={sw1:02X}{sw2:02X}")
        # 비프음 (실패해도 본 흐름은 계속)
        try:
            card_service.connection.transmit(_BEEP_APDU)
        except Exception:
            logger.debug("비프 APDU 실패 (무시)")
        return normalize_uid(bytes(response).hex())
    except (CardConnectionException, NoCardException) as e:
        raise ReaderUnavailableError(f"카드 통신 실패: {e}") from e
    finally:
        try:
            card_service.connection.disconnect()
        except Exception:
            logger.exception("리더 disconnect 실패")


async def scan_card_uid(timeout_sec: int | None = None) -> str:
    """등록 리더에서 카드 한 장 읽고 UID(정규화) 반환.

    pyscard는 동기 블로킹이라 별도 스레드에서 실행.
    """
    timeout = timeout_sec if timeout_sec is not None else settings.READER_TIMEOUT_SEC
    return await asyncio.to_thread(_read_uid_blocking, timeout)
