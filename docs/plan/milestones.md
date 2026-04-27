# Implementation Milestones

구현 순서 / 의존 관계 / 단계별 deliverable.

원칙:
- **수직 슬라이스 우선** — 한 페이즈 끝나면 뭐든 동작하는 상태
- **로컬 우선** — macOS dev 머신에서 다 만들고 마지막에 Pi/집서버 배포
- **하드웨어는 늦게** — 스펙/스키마/API 다 정해진 후 ACR122U 결합

---

## Phase 0 — 환경 부트스트랩 ✅
**Goal:** 빈 monorepo에 3개 컴포넌트 폴더 + 공통 설정

- [x] 루트 `.gitignore` (Python/Node/OS/Editor/`.env*` 등)
- [x] 루트 `.env.example` ([[../architecture/security#시크릿-인벤토리]] 따름)
- [x] `docker-compose.yml` — Postgres 17-alpine. 호스트 포트는 [[../conventions/common#포트-컨벤션]] 따름
- [x] `backend/`, `agent/`, `admin/` 폴더 + `.gitkeep`

**Deliverable:** `docker compose up -d` → Postgres 17.9 healthy 확인 (2026-04-27).

---

## Phase 1 — 백엔드 스켈레톤 + 스키마 ✅
**Goal:** FastAPI 앱이 뜨고, 마이그레이션이 적용되고, `/health`가 200

- [x] `backend/` Python 프로젝트 셋업 (uv), 의존성 설치
- [x] `app/core/config.py` — env 로드 (root `.env` 참조)
- [x] `app/db/base.py`, `app/db/models.py` — SQLAlchemy 모델
- [x] Alembic 초기화 + 첫 마이그레이션 (3 테이블 + enum + `updated_at` 트리거)
- [x] `app/main.py` — lifespan에서 `asyncio.to_thread(run_migrations)` (alembic의 자체 asyncio.run 충돌 회피)
- [x] `GET /health` 엔드포인트
- [x] `scripts/create_admin.py` — bcrypt 직접 사용 (passlib 미사용, 4.x 호환 이슈)

**Deliverable:** `uvicorn app.main:app --port 48000` → `curl /health` 200, admin 1명 시드 확인 (2026-04-27).

---

## Phase 2 — 인증 (admin 로그인) ✅
**Goal:** 비밀번호로 JWT 발급 + 보호된 엔드포인트 검증

- [x] `app/core/security.py` — bcrypt 해싱 + JWT (HS256, 30일 TTL)
- [x] `app/core/deps.py` — `CurrentUser` (Bearer 검증) / `AgentAuth` (X-Agent-Key 검증)
- [x] `app/repos/user_repo.py`, `app/services/auth_service.py`, `app/schemas/auth.py`, `app/api/auth.py` — 레이어 분리
- [x] `POST /api/auth/login`, `GET /api/auth/me`
- [x] CORS 미들웨어 (Phase 1에서 셋업)
- [x] `scripts/create_admin.py`도 `core/security.hash_password`로 위임 (DRY)

**Deliverable:** 6 케이스 통합 테스트 통과 (login 성공/실패, me 누락/유효/만료유사).

---

## Phase 3 — 사용자 / 카드 CRUD (스캔 제외) ✅
**Goal:** 카드 등록만 빼고 나머지 데이터 조작 다 됨

- [x] `core/uid.py` — UID 정규화 헬퍼 + `InvalidUidError`
- [x] `core/exceptions.py` — 도메인 예외 (UserNotFound/CardNotFound/CardUidConflict)
- [x] `dtos/users.py` — `UserListItem` (User + card_count + last_access_at)
- [x] `repos/user_repo.py` — list_with_aggregates JOIN 쿼리, add, update
- [x] `repos/card_repo.py` — list_all, add, update
- [x] `services/user_service.py`, `services/card_service.py`
- [x] `schemas/users.py`, `schemas/cards.py`
- [x] `GET/POST/PATCH /api/users`, `GET/POST/PATCH /api/cards`
- [x] UID UNIQUE 충돌 시 409, hex 아님 시 422, 존재하지 않는 user_id 404

**Deliverable:** 9 케이스 통합 통과. UID `"59:fa:c3:03"` → `"59FAC303"` 정규화 동작.

---

## Phase 4 — 등록 리더(#2) 연동 ✅
**Goal:** `POST /api/cards/scan`이 실제로 카드 읽음

- [x] `app/services/card_reader.py` — pyscard `CardRequest` 래퍼, `asyncio.to_thread`로 블로킹 격리
- [x] `app/core/exceptions`에 `ReaderUnavailableError`, `CardScanTimeoutError`
- [x] `POST /api/cards/scan` (JWT 보호, 408/503)
- [x] 부저 끄기 APDU(`FF 00 52 00 00`) 추가 — 사무실에서 조용히 테스트
- [x] 401, 503 (리더 미연결), 408 (timeout), 200 (실제 카드 → UID `9E4BC303`) 전 케이스 검증

---

## Phase 5 — 출입 엔드포인트 ✅ (MVP 기준선)
**Goal:** Pi 에이전트가 보낼 인터페이스 완성

- [x] `schemas/access.py` — AccessRequest / AccessResponse
- [x] `repos/card_repo.find_active_by_uid` (UID로 활성 카드 조회)
- [x] `repos/access_log_repo.add` (성공/거부 모두 INSERT)
- [x] `services/access_service.record_access` — 정규화 → 카드 → 사용자 → 판정 → 로그
- [x] `POST /api/access` (X-Agent-Key 인증)

**Deliverable:** 7 케이스 + DB 검증 통과
- 401 (키 없음/잘못됨), 422 (hex 아님)
- 미등록 UID → allowed:false (card_id/user_id NULL)
- 비활성 사용자 → allowed:false (card_id/user_id 채워짐)
- 활성 → allowed:true
- UID 다른 포맷(`59:fa:c3:03`)도 같은 카드로 인식 (정규화 동작)
- KST→UTC 변환 정상

---

## Phase 6 — NFC 에이전트 ✅ (풀 사이클 완성)
**Goal:** 카드 태그하면 백엔드로 push 가는 단순 데몬

- [x] `agent/` Python 프로젝트 (uv, pyproject.toml)
- [x] `nfc_agent/config.py` — root `.env` 공유
- [x] `nfc_agent/reader.py` — pyscard `CardRequest(newcardonly=True)`, 모듈 레벨 디바운스, 부저 끄기 APDU
- [x] `nfc_agent/client.py` — httpx `POST /api/access`, BackendError 정의
- [x] `nfc_agent/feedback.py` — 결과 로그 (GPIO LED는 추후)
- [x] `nfc_agent/main.py` + `__main__.py` — `python -m nfc_agent` 진입점
- [x] `systemd/nfc-agent.service` — Pi 배포 대비 유닛 파일

**Deliverable:** macOS에서 풀 사이클 검증 완료
- 카드 6번 태그 → access_logs 6 row, 각각 단일 처리 (디바운스 동작)
- UID `9E4BC303` (실제 카드) → allowed:true (등록된 카드)
- 부저 음소거 (첫 카드 외 무음)
- 리더 미연결 시 ReaderError로 깨끗하게 종료

---

## Phase 7 — Logs / Stats API ✅
**Goal:** 관리자 웹에서 보여줄 데이터 다 준비됨

- [x] `dtos/access.py` — cursor 인코드/디코드 (base64 JSON)
- [x] `repos/access_log_repo.list_paginated` — `(occurred_at, id) DESC` 튜플 비교
- [x] `repos/access_log_repo.daily_stats` / `monthly_stats` — KST 04:00 컷오프 raw SQL
- [x] `services/log_service`, `services/stats_service` — 시간 변환 + 포맷 (HH:MM)
- [x] `schemas/logs`, `schemas/stats` — 응답 모델
- [x] `GET /api/logs` (filter + cursor pagination)
- [x] `GET /api/stats/daily?user_id=&year=&month=`
- [x] `GET /api/stats/monthly?user_id=&year=`

**Deliverable:** 검증 완료
- /api/logs: 580건 중 limit=3 → next_cursor 정상 반환, allowed=true 필터 동작
- /api/stats/daily 2026-04: 1 day, 10:01-18:01 (480분, KST 변환 정상)
- /api/stats/monthly 2026: 04월 work_days=1, avg 10:01/18:02

---

## Phase 8 — 관리자 웹 스켈레톤 + 인증 ✅
**Goal:** Next.js 앱에서 로그인 → 토큰 → 보호된 라우트 진입

- [x] `admin/` Next.js 16 + TypeScript + Tailwind 4 (create-next-app)
- [x] shadcn 패턴 수동 셋업 (`components.json`, `lib/utils.ts`, `Button` / `Input`)
- [x] `lib/api/client.ts` — axios 인스턴스, JWT 자동 부착 interceptor, 401 → /login 리다이렉트
- [x] `lib/api/{auth,users,cards,logs,stats}.ts` — 타입 있는 API 함수
- [x] `lib/types/index.ts` — 백엔드 schema 1:1 매칭
- [x] `app/login/page.tsx` — 비밀번호 폼
- [x] `app/(authed)/layout.tsx` — 토큰 가드 + nav
- [x] 포트 43000 (port convention)
- [x] react-hooks/set-state-in-effect 룰 완화 (Next 16 새 룰, 1인 스코프 무관)

---

## Phase 9 — 관리자 웹 페이지 ✅
**Goal:** 5개 페이지 다 동작

- [x] `/logs` — 출입 로그 표 + 허용/거부 필터 + 더보기 (cursor)
- [x] `/users` — 목록(card_count, last_access_at), 추가, active 토글
- [x] `/users/[id]` — 상세 + 카드 등록 (POST /scan → UID → 라벨 → 저장), 카드 분실 토글
- [x] `/stats` — 일별/월별 토글 + 사용자/년/월 필터

**Deliverable:** 4 페이지 200 응답, /login HTML 마커 검증. 풀 워크플로(로그인 → 사용자/카드 등록 → 출입 → 로그/통계 조회) 가능.

---

## Phase 10 — 배포
**Goal:** 운영 환경 동작

### 10-A. 집 서버 (백엔드 + DB + 등록 리더)
- [ ] Postgres 운영 DB 셋업 (Docker 또는 native)
- [ ] 백엔드 systemd 또는 Docker 기동
- [ ] 등록용 ACR122U 집 서버 USB 연결
- [ ] Nginx server block + HTTPS 인증서 ([[../architecture/security#네트워크--https]])
- [ ] 방화벽 / 포트 정책 ([[../architecture/security#네트워크--https]])
- [ ] DB 백업 cron ([[../architecture/security#백업]])

### 10-B. Vercel (admin web)
- [ ] Vercel 프로젝트 연결, Root Directory `admin/`
- [ ] 환경변수 `NEXT_PUBLIC_API_BASE_URL` 설정
- [ ] CORS allow_origins에 Vercel 도메인 추가

### 10-C. 라즈베리파이 (출입용 리더 + 에이전트)
- [ ] Pi OS 64bit 설치, `libnfc` / `pcscd` 설치
- [ ] `nfc-list`로 출입용 ACR122U 인식 확인
- [ ] `agent/` 코드 배포 (`/opt/nfc-agent`)
- [ ] `/etc/nfc-agent.env` 작성 (API_BASE_URL, AGENT_API_KEY)
- [ ] systemd 서비스 등록 + enable
- [ ] **사무실 출입문 옆 설치, 첫 카드 태그 테스트**

**Deliverable:** 사무실에서 카드 찍으면 집 백엔드에 기록, Vercel admin에서 조회 가능.

---

## 의존 관계 그래프

```
Phase 0 ─ Phase 1 ─ Phase 2 ─┬─ Phase 3 ─ Phase 4 ─ Phase 5 ─ Phase 6
                              │
                              └─ Phase 7 (Logs/Stats API)
                                   │
                              Phase 8 ─ Phase 9
                                   │
                                Phase 10 (배포, 마지막)
```

- Phase 6/7은 의존 없으므로 병렬 가능
- Phase 8은 Phase 2(인증) 이후 언제든 가능, Phase 9는 Phase 7 결과 필요
- 하드웨어 검증은 Phase 4 / 6에 분산되어 있음 (한 번에 모이지 않게)

## 우선순위 메모

- **MVP 기준선** = Phase 5까지 완료 (백엔드 + Pi 에이전트로 출입 기록만 됨)
- Phase 7-9는 사용성 보강 (관리자 웹)
- Phase 10은 코드 안정화된 후 마지막에

## 참고

- [[../architecture/overview]]
- [[../architecture/repo-layout]]
- [[../MAP]]
