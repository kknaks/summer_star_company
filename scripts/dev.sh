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
  for pid in "${PIDS[@]}"; do
    kill -TERM "$pid" 2>/dev/null || true
  done
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
