#!/usr/bin/env bash
# 로컬 dev — 백엔드 (FastAPI) host에서 실행.
# Docker 대신 host로 띄워야 USB(ACR122U)에 접근 가능.

set -euo pipefail
cd "$(dirname "$0")/../backend"

if [ ! -d .venv ]; then
  echo "─ .venv 없음, 의존성 설치 중 ─"
  uv sync
fi

# .env가 root에 있어 ROOT_DIR로 자동 로드됨
exec uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 48000
