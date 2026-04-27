"""메인 루프 — 카드 태그 → 백엔드 push → 피드백.

의도적 단순화: 로컬 캐시/큐/오프라인 폴백 없음 (docs/spec/nfc-agent#책임).
실패 시 사용자가 재태그하면 됨.
"""

import logging
import sys
from datetime import UTC, datetime

from nfc_agent.client import BackendClient, BackendError
from nfc_agent.config import settings
from nfc_agent.feedback import signal_result
from nfc_agent.reader import ReaderError, wait_for_card

logger = logging.getLogger("nfc_agent")


def main() -> int:
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
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
