# 문서 인덱스 (MAP)

이 프로젝트의 모든 문서 진입점. **새 문서를 만들면 반드시 이 표에 등록.**

상태 표기:
- 🟢 결정됨 — 합의 완료
- 🟡 진행 중 — 일부 결정, 일부 미정
- ⚪ 비어있음 — placeholder만 존재
- ⏸ 보류 — 스코프 외, 향후 검토

## Architecture

| 문서 | 목적 | 상태 |
|---|---|---|
| [[architecture/overview]] | 전체 시스템 구조 / 4컴포넌트 / 인증 / 운영 | 🟡 진행 중 |
| [[architecture/repo-layout]] | monorepo 디렉토리 구조 | 🟢 |
| [[architecture/security]] | 시크릿 / HTTPS / 백업 / Pi 보안 | 🟢 |
| [[architecture/deployment-pi]] | Pi 셋업, systemd 서비스 등록 | ⚪ (실제 배포 시) |

## Domain

| 문서 | 목적 | 상태 |
|---|---|---|
| [[domain/user]] | 사용자 모델, 권한, 등록 흐름 | 🟢 |
| [[domain/card]] | NFC 카드 모델, UID 정규화, 등록/회수 | 🟢 |
| [[domain/access-log]] | 출입 로그, 출/퇴근 해석(KST 04:00 컷오프) | 🟢 |
| [[domain/reader]] | 리더기 메타 모델 | ⏸ (1대 전제, 보류) |

## Spec (컴포넌트별 상세)

| 문서 | 목적 | 상태 |
|---|---|---|
| [[spec/database]] | Postgres 스키마, 마이그레이션, 인덱스 | 🟢 |
| [[spec/backend-api]] | FastAPI 엔드포인트, 인증 미들웨어, 등록 리더 연동 | 🟢 |
| [[spec/nfc-agent]] | Pi에서 도는 Python 에이전트, 카드 감시 + 백엔드 push (단순 데몬) | 🟢 |
| [[spec/admin-web]] | Next.js 관리자 대시보드 (Vercel) | 🟢 |

## Conventions

| 문서 | 목적 | 상태 |
|---|---|---|
| [[conventions/common]] | 언어 무관 공통 (커밋, 주석, 시크릿) | 🟢 |
| [[conventions/python]] | backend + agent (레이어 구조 명시) | 🟢 |
| [[conventions/typescript]] | admin (Next.js 레이어 구조 명시) | 🟢 |

## Plan

| 문서 | 목적 | 상태 |
|---|---|---|
| [[plan/milestones]] | 마일스톤 / 단계별 작업 순서 | 🟢 |

## 관계 그래프 (개념)

```
overview ──┬── domain/user ──── card ──── access-log
           │       │              │            │
           │       └──────────────┴────────────┘
           │
           ├── architecture/repo-layout
           ├── architecture/security
           ├── spec/database  ← (domain 3개 종합)
           ├── spec/backend-api  ← (database + auth + 등록 리더)
           ├── spec/nfc-agent    ← (backend-api/access)
           └── spec/admin-web    ← (backend-api)
```

## SSOT 규칙

각 결정은 **owner 문서 한 곳에만** 작성. 나머지 문서는 위키링크로 참조. 변경 시 owner만 수정.

| 영역 | SSOT 위치 |
|---|---|
| 도메인 결정 (User/Card/AccessLog 속성·규칙) | `docs/domain/*` |
| 컴포넌트 구현 (스키마·엔드포인트·라이브러리) | `docs/spec/*` |
| 크로스컷팅 (인증·보안·네트워크 복원성) | `docs/architecture/*` |
| 요약/진입점 (디테일 X, 링크 O) | `docs/architecture/overview.md` |

## 작업 규칙 요약

- 위키링크 형식 `[[domain/user]]` / `[[domain/user#속성]]` 사용 (옵시디언 그래프뷰 활용)
- 새 문서 만들면 위 표에 한 줄 등록
- 결정 미뤄둔 항목은 각 문서 끝 "결정 필요" 섹션에 체크박스로 모음
