---
name: code-validation
description: 코드 작성 후 자동 검증 절차. lint/format/타입체크 실행. Stop 훅에서 호출.
---

# Code Validation Skill

코드 변경 후 자동으로 돌릴 검증 단계.

검증 절차 (TBD):

**Backend (Python)**
- `cd backend && ruff check .` — 린트
- `cd backend && ruff format --check .` — 포맷
- 추후 mypy 도입 시 추가

**Agent (Python)**
- `cd agent && ruff check .`
- `cd agent && ruff format --check .`

**Frontend (TypeScript)**
- `cd admin && pnpm lint` (or `npm run lint`)
- `cd admin && pnpm typecheck` (or `tsc --noEmit`)
- `cd admin && pnpm format:check`

레이어 위반 체크 (수동/grep):
- 백엔드 router에서 SQLAlchemy import 검사
- 프론트 컴포넌트에서 axios import 검사

> 본문 추후 보강. ruff/eslint 설정 파일은 각 컴포넌트 구현 시 추가.
