#!/usr/bin/env bash
# 로컬 dev 풀스택 한 번에:
#   - postgres + backend: docker
#   - admin (Next.js): host pnpm dev
#   - agent (NFC): host uv run
#
# Ctrl+C 한 번에 모두 종료.

set -euo pipefail
cd "$(dirname "$0")/.."

# 출력 prefix 헬퍼 (macOS sed/GNU sed 차이 회피용 awk)
prefix() {
  awk -v p="$1" '{print p $0; fflush()}'
}

# 1) docker 부팅 (postgres + backend)
./scripts/dev-up.sh

PIDS=()

cleanup() {
  echo
  echo "── 종료 신호 — 정리 중 ──"
  # 1. 알려진 자식 (awk pipeline 끝의 PID) 종료
  for pid in "${PIDS[@]}"; do
    kill -TERM "$pid" 2>/dev/null || true
  done
  # 2. port 43000 점유 프로세스 (next dev) — pnpm dev는 자식을 직접 안 죽여서 보강
  if command -v lsof >/dev/null 2>&1; then
    lsof -ti :43000 2>/dev/null | xargs -r kill -TERM 2>/dev/null || true
  fi
  # 3. agent 프로세스 (다른 프로젝트와 충돌 X — 패턴 명확)
  pkill -TERM -f "python -m nfc_agent" 2>/dev/null || true
  pkill -TERM -f "summer_star_company/admin" 2>/dev/null || true
  sleep 1
  # 4. 강제 종료 (안 죽었으면)
  if command -v lsof >/dev/null 2>&1; then
    lsof -ti :43000 2>/dev/null | xargs -r kill -KILL 2>/dev/null || true
  fi
  pkill -KILL -f "python -m nfc_agent" 2>/dev/null || true
  pkill -KILL -f "summer_star_company/admin" 2>/dev/null || true
  wait 2>/dev/null || true
  docker compose down
  echo "✓ 모두 종료"
}
trap cleanup INT TERM

# 2) admin
(./scripts/dev-admin.sh 2>&1 | prefix "[admin] ") &
PIDS+=($!)

# 3) agent
(./scripts/dev-agent.sh 2>&1 | prefix "[agent] ") &
PIDS+=($!)

cat <<'EOF'

── 풀스택 실행 중 ──
  admin:   http://localhost:43000
  backend: http://localhost:48000  (docker)
  agent:   호스트 uv run

종료: Ctrl+C
EOF

wait
