"""출입 결과 피드백. ACR122U 내장 비프/LED 기본 동작에 의존.

GPIO 외부 LED/부저는 추후 (docs/spec/nfc-agent#추후-고려).
현재는 로그 출력 + 카드 detect 시 ACR122U 자동 비프음으로 충분.
"""

import logging

logger = logging.getLogger(__name__)


def signal_result(allowed: bool) -> None:
    if allowed:
        logger.info("✓ 통과")
    else:
        logger.info("✗ 거부")
