# summer_star_company

NFC 카드 기반 사무실 출퇴근 트래킹 시스템.

## 스코프

- **개인 사무실용** — 본인 1명이 admin, 직원 소수, 리더기(Raspberry Pi) 1대
- 멀티테넌트/SaaS 아님. RBAC, 조직 모델, OTA 배포 등 기업용 패턴 도입 금지

## 아키텍처 (4 컴포넌트)

```
[ACR122U] ─USB─ [Pi: Python Agent] ─HTTP─> [FastAPI Backend] ─SQL─> [Postgres]
                                                  ↑
                                          [Next.js 관리자 웹]
```

- **에이전트**: Python (`pyscard`/`nfcpy`) — Pi에 배포, macOS에서 로컬 개발
- **백엔드**: FastAPI
- **DB**: Postgres (집 서버 자호스팅, Docker)
- **프론트**: Next.js (관리자 대시보드)

## 인증

- 관리자 웹: 비밀번호 → **JWT 30일 + localStorage** (stateless, sessions 테이블 없음). 해싱 `passlib[bcrypt]`
- 에이전트→백엔드: 정적 API 키 (`X-Agent-Key` 헤더)
- OAuth/세션쿠키 사용 안 함
- SSOT: [[domain/user#인증]]

## 문서 작업 규칙

- **모든 문서 인덱스는 [docs/MAP.md](docs/MAP.md)** — 새 작업 들어가기 전 먼저 읽기
- **SSOT 규칙**: 각 결정/사실은 owner 문서 한 곳에만 적고, 나머지는 위키링크로 참조. 결정이 바뀌면 owner 문서만 수정 (다른 문서들은 링크 그대로라 자동으로 따라옴)
  - 도메인 결정 (User, Card, AccessLog 속성/규칙) → `docs/domain/*` 가 SSOT
  - 컴포넌트 구현 (스키마, 엔드포인트, 라이브러리) → `docs/spec/*` 가 SSOT
  - 크로스컷팅 (인증, 보안, 네트워크 복원성) → `docs/architecture/*` 가 SSOT
  - `architecture/overview.md` 는 **요약 문서** — 디테일 적지 말고 링크
- 위키링크 `[[path/name]]` 형식 사용 (옵시디언 그래프뷰 호환)
- 새 문서 만들면 `docs/MAP.md`에 한 줄 등록
- 결정 미뤄둔 항목은 각 문서 끝 "결정 필요" 체크박스로 모음

## 디렉토리

- `docs/architecture/` — 전체 구조
- `docs/domain/` — 도메인 모델 (user, card, access-log)
- `docs/spec/` — 컴포넌트별 상세 스펙
- `docs/plan/` — 작업 계획 / 마일스톤
- `.claude/` — agents, skills, hooks, commands (필요 시)
