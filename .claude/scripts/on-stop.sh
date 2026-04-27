#!/usr/bin/env bash
# Stop hook — 응답 완료 후 코드/문서 변경 감지 시 체크리스트 강제 출력
# stdout 출력은 다음 턴 Claude 컨텍스트로 주입됨

set -eu

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$PROJECT_DIR" || exit 0
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

CHANGED=$(git status --porcelain 2>/dev/null || true)
if [ -z "$CHANGED" ]; then
  exit 0
fi

CHECKLIST_FILE="$PROJECT_DIR/.claude/skills/code-checklist/SKILL.md"
if [ ! -f "$CHECKLIST_FILE" ]; then
  exit 0
fi

cat <<'HEADER'
[hook:on-stop] ⚠️ 변경 감지 — 다음 응답에서 아래 체크리스트를 본문에 명시적으로 점검하세요.
각 항목 옆에 ✓(OK) 또는 ⚠(보완 필요) 표시 후 마무리. 누락 시 "작업 완료" 선언 금지.

──────── code-checklist ────────
HEADER

# 체크리스트 항목만 추출
grep -E '^- \[ \]' "$CHECKLIST_FILE" || true

cat <<'FOOTER'
────────────────────────────────

변경된 파일:
FOOTER

git status --short
