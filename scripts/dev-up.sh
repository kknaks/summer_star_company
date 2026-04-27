#!/usr/bin/env bash
# 로컬 dev 인프라 (postgres + backend) docker로 부팅.
# admin / agent는 호스트에서 별도 스크립트로.

set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "⚠ .env 없음 — .env.example 복사"
  cp .env.example .env
fi

docker compose up -d
echo
echo "─── 컨테이너 ───"
docker compose ps

cat <<'EOF'

다음 단계 (별도 터미널에서):
  ./scripts/dev-admin.sh   # 관리자 웹 (http://localhost:43000)
  ./scripts/dev-agent.sh   # NFC 에이전트 (USB 리더 필요)

종료: ./scripts/dev-down.sh
EOF
