"""백엔드 HTTP 클라이언트. /api/access push."""

import logging
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)


class BackendError(Exception):
    pass


class BackendClient:
    def __init__(self, base_url: str, api_key: str, timeout_sec: float):
        self._client = httpx.Client(
            base_url=base_url,
            headers={"X-Agent-Key": api_key},
            timeout=timeout_sec,
        )

    def post_access(self, uid: str, occurred_at: datetime) -> bool:
        """`POST /api/access` 호출 → allowed 반환. 실패 시 BackendError."""
        try:
            response = self._client.post(
                "/api/access",
                json={"uid": uid, "occurred_at": occurred_at.isoformat()},
            )
        except httpx.RequestError as e:
            raise BackendError(f"네트워크 실패: {e}") from e

        if response.status_code != 200:
            raise BackendError(f"비정상 응답 {response.status_code}: {response.text}")

        try:
            return bool(response.json()["allowed"])
        except (KeyError, ValueError) as e:
            raise BackendError(f"응답 페이로드 오류: {response.text}") from e

    def close(self) -> None:
        self._client.close()
