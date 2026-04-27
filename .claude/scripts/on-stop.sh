#!/usr/bin/env bash
# Stop hook — 응답 완료 후 코드 변경이 있으면 검증 안내
# 변경 없으면 조용히 종료

set -eu

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

# git 추적 안 되는 디렉토리면 무시
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

CHANGED=$(git status --porcelain 2>/dev/null || true)
if [ -z "$CHANGED" ]; then
  exit 0
fi

cat <<'EOF'
[hook:on-stop] 변경된 파일 있음. 응답 완료 전 점검 권고:
- 컨벤션 준수 확인 (skills/code-convention)
- 코드 체크리스트 (skills/code-checklist) — 매직넘버/타입힌트/SSOT
- lint 실행 (skills/code-validation)
- 새 문서 만들었으면 docs/MAP.md 등록
EOF
