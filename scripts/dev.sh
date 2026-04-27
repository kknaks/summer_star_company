#!/usr/bin/env bash
# 로컬 dev 풀스택 한 번에:
#   postgres: docker
#   backend / admin / agent: host (USB 접근 위해)
#
# Ctrl+C 한 번에 모두 종료.

set -euo pipefail
cd "$(dirname "$0")/.."

prefix() {
  awk -v p="$1" '{print p $0; fflush()}'
}

# 1) postgres 부팅
./scripts/dev-up.sh

PIDS=()

cleanup() {
  echo
  echo "── 종료 신호 — 정리 중 ──"
  # awk pipeline 끝 PID
  for pid in "${PIDS[@]}"; do
    kill -TERM "$pid" 2>/dev/null || true
  done
  # 포트/패턴 기반 강제 정리 (pnpm/uvicorn/agent가 awk 죽인다고 따라죽지 않음)
  if command -v lsof >/dev/null 2>&1; then
    lsof -ti :43000 :48000 2>/dev/null | xargs -r kill -TERM 2>/dev/null || true
  fi
  pkill -TERM -f "python -m nfc_agent" 2>/dev/null || true
  pkill -TERM -f "summer_star_company/admin" 2>/dev/null || true
  pkill -TERM -f "summer_star_company/backend" 2>/dev/null || true
  sleep 1
  if command -v lsof >/dev/null 2>&1; then
    lsof -ti :43000 :48000 2>/dev/null | xargs -r kill -KILL 2>/dev/null || true
  fi
  pkill -KILL -f "python -m nfc_agent" 2>/dev/null || true
  pkill -KILL -f "summer_star_company/admin" 2>/dev/null || true
  pkill -KILL -f "summer_star_company/backend" 2>/dev/null || true
  wait 2>/dev/null || true
  docker compose down
  echo "✓ 모두 종료"
}
trap cleanup INT TERM

# 2) backend (host)
(./scripts/dev-backend.sh 2>&1 | prefix "[backend] ") &
PIDS+=($!)

# postgres 헬시 + backend 부팅 대기
sleep 3

# 3) admin
(./scripts/dev-admin.sh 2>&1 | prefix "[admin]   ") &
PIDS+=($!)

# 4) agent
(./scripts/dev-agent.sh 2>&1 | prefix "[agent]   ") &
PIDS+=($!)

cat <<'EOF'

── 풀스택 실행 중 ──
  postgres: docker (port 45432)
  backend:  http://localhost:48000  (host, USB 접근 가능)
  admin:    http://localhost:43000
  agent:    호스트 uv run

종료: Ctrl+C
EOF

wait
