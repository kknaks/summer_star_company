#!/usr/bin/env bash
# 로컬 dev — Next.js admin 웹 (http://localhost:43000).
# pnpm 필요. 의존성 미설치 시 자동으로 install.

set -euo pipefail
cd "$(dirname "$0")/../admin"

if [ ! -d node_modules ]; then
  echo "─ node_modules 없음, 설치 중 ─"
  pnpm install
fi

exec pnpm dev
