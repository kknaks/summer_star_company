"""출입용 리더(#1) 감시. pyscard CardRequest 블로킹.

UID 정규화 정책: docs/domain/card.md (대문자 hex, 구분자 제거).
backend의 normalize_uid와 의도적 중복 — repo-layout.md 참고.
"""

import contextlib
import logging
import threading
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


class AgentStoppedError(Exception):
    """SIGINT/SIGTERM 등 종료 요청에 의해 wait_for_card가 중단됨."""


# ACR122U PSEUDO-APDU: GET DATA — UID 조회
_GET_UID_APDU = [0xFF, 0xCA, 0x00, 0x00, 0x00]
# ACR122U one-shot 비프: LED 변경 없음(LL=00), T1=100ms, 1회, 부저 ON.
# 펌웨어 영구설정(FF 00 52)이 disable로 박혀도 능동 트리거라 항상 소리 남.
_BEEP_APDU = [0xFF, 0x00, 0x40, 0x00, 0x04, 0x01, 0x00, 0x01, 0x01]
# 1초 단위로 깨어나 stop 플래그 체크 — Ctrl+C 빠르게 반응
_POLL_TIMEOUT_SEC = 1

# 외부(메인 시그널 핸들러)에서 set → wait_for_card가 다음 폴링 사이클에서 AgentStopped raise
_stop_event = threading.Event()


def request_stop() -> None:
    _stop_event.set()


def reset_stop() -> None:
    _stop_event.clear()


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


def _wait_for_removal(target_reader) -> None:
    """카드가 물리적으로 제거될 때까지 짧은 폴링으로 대기.

    같은 카드를 리더 위에 계속 올려둔 상태에서 재발사 폭주 방지.
    stop 요청 시 즉시 종료.
    """
    while not _stop_event.is_set():
        try:
            cr = CardRequest(
                readers=[target_reader],
                timeout=0.3,
                cardType=AnyCardType(),
            ).waitforcard()
            with contextlib.suppress(Exception):
                cr.connection.disconnect()
            time.sleep(0.2)  # 여전히 있음 — 잠깐 쉬고 다시 체크
        except CardRequestTimeoutException:
            return  # 카드 없음 → 제거 확인


def wait_for_card() -> str:
    """카드 한 장 대기 후 UID(정규화) 반환.

    처리 후 카드 제거까지 블로킹 — 같은 카드 연속 재발사 방지.
    request_stop()이 호출되면 AgentStopped 예외 raise.
    """
    target_reader = _find_reader()

    while True:
        if _stop_event.is_set():
            raise AgentStoppedError()
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
            response, sw1, sw2 = card_service.connection.transmit(_GET_UID_APDU)
            if sw1 != 0x90 or sw2 != 0x00:
                raise ReaderError(f"GET_UID APDU 비정상 SW={sw1:02X}{sw2:02X}")
            uid = _normalize_uid(bytes(response).hex())
            # 비프음 (실패해도 본 흐름은 계속)
            try:
                card_service.connection.transmit(_BEEP_APDU)
            except Exception:
                logger.debug("비프 APDU 실패 (무시)")
        except (CardConnectionException, NoCardException):
            time.sleep(0.3)
            continue
        finally:
            try:
                card_service.connection.disconnect()
            except Exception:
                logger.exception("리더 disconnect 실패")

        # 다음 read 전에 물리적 제거 확인
        _wait_for_removal(target_reader)
        return uid
