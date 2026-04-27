#!/usr/bin/env bash
# 로컬 dev — NFC 에이전트 실행.
# 카드 리더(ACR122U)가 호스트 USB에 꽂혀있어야 함. uv 필요.
#
# 환경변수는 root .env에서 자동 로드 (API_BASE_URL, AGENT_API_KEY 등).
# 종료: Ctrl+C (1초 안에 정상 종료)

set -euo pipefail
cd "$(dirname "$0")/../agent"

if [ ! -d .venv ]; then
  echo "─ .venv 없음, 의존성 설치 중 ─"
  uv sync
fi

exec uv run python -m nfc_agent
