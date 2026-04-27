#!/usr/bin/env bash
# 로컬 dev 인프라 종료 (postgres + backend).
# 데이터(volume)는 보존 — 완전 초기화는 `docker compose down -v`.

set -euo pipefail
cd "$(dirname "$0")/.."

docker compose down
echo "✓ docker stopped (volume 보존됨)"
