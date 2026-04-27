#!/usr/bin/env bash
# 로컬 dev 인프라 — postgres만 docker.
# backend/admin/agent는 host (USB 접근 등 이유로).

set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "⚠ .env 없음 — .env.example 복사"
  cp .env.example .env
fi

docker compose up -d postgres
echo
echo "─── postgres 컨테이너 ───"
docker compose ps postgres

cat <<'EOF'

다음 단계 (별도 터미널에서):
  ./scripts/dev-backend.sh   # FastAPI (http://localhost:48000) — USB 접근 가능
  ./scripts/dev-admin.sh     # Next.js  (http://localhost:43000)
  ./scripts/dev-agent.sh     # NFC 에이전트 (USB 리더 필요)

또는 한 번에: ./scripts/dev.sh
종료: ./scripts/dev-down.sh
EOF
