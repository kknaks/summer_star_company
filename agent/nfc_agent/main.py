"""메인 루프 — 카드 태그 → 백엔드 push → 피드백.

의도적 단순화: 로컬 캐시/큐/오프라인 폴백 없음 (docs/spec/nfc-agent#책임).
실패 시 사용자가 재태그하면 됨.
"""

import logging
import signal
import sys
from datetime import UTC, datetime

from nfc_agent import reader as reader_mod
from nfc_agent.client import BackendClient, BackendError
from nfc_agent.config import settings
from nfc_agent.feedback import signal_result
from nfc_agent.reader import AgentStoppedError, ReaderError, wait_for_card

logger = logging.getLogger("nfc_agent")


def _on_signal(signum: int, _frame) -> None:  # noqa: ANN001
    logger.info("종료 신호 수신 (signum=%s) — 즉시 종료 절차 시작", signum)
    reader_mod.request_stop()


def main() -> int:
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    signal.signal(signal.SIGINT, _on_signal)
    signal.signal(signal.SIGTERM, _on_signal)
    logger.info(
        "NFC agent 시작 — base=%s reader=%s",
        settings.API_BASE_URL,
        settings.READER_NAME,
    )

    client = BackendClient(
        base_url=settings.API_BASE_URL,
        api_key=settings.AGENT_API_KEY,
        timeout_sec=settings.HTTP_TIMEOUT_SEC,
    )

    try:
        while True:
            try:
                uid = wait_for_card()
            except AgentStoppedError:
                logger.info("정상 종료")
                return 0
            except ReaderError as e:
                logger.error("리더 에러: %s", e)
                return 1
            except KeyboardInterrupt:
                logger.info("사용자 중단")
                return 0

            occurred_at = datetime.now(UTC)
            try:
                allowed = client.post_access(uid, occurred_at)
            except BackendError as e:
                logger.warning("백엔드 push 실패: %s — 재태그 필요", e)
                allowed = False

            logger.info("UID=%s allowed=%s", uid, allowed)
            signal_result(allowed)
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())
