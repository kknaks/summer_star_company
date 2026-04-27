#!/usr/bin/env bash
# UserPromptSubmit hook — 작업 전 컨텍스트 안내
# stdout 출력은 사용자 프롬프트에 컨텍스트로 추가됨

set -eu

cat <<'EOF'
[hook:on-prompt] 작업 전 체크리스트:
1. docs/MAP.md 확인 → 관련 문서 식별
2. 작업 영역 컨벤션 적용 (backend/agent → conventions/python, admin → conventions/typescript)
3. SSOT 규칙 — 결정사항은 owner 문서에만 (overview는 요약+링크)
4. 코드 변경 시 레이어 규칙 준수 (router/component → 직접 DB/axios 호출 X)
EOF
