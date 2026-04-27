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
- [x] `docker-compose.yml` — Postgres 17-alpine, 호스트 포트 **5440** (5432/5433은 다른 컨테이너가 점유)
- [x] `backend/`, `agent/`, `admin/` 폴더 + `.gitkeep`

**Deliverable:** `docker compose up -d` → Postgres 17.9 healthy 확인 (2026-04-27).

---

## Phase 1 — 백엔드 스켈레톤 + 스키마
**Goal:** FastAPI 앱이 뜨고, 마이그레이션이 적용되고, `/health`가 200

- [ ] `backend/` Python 프로젝트 셋업, 의존성 설치 ([[../spec/backend-api#기술-스택]] 참고)
- [ ] `app/core/config.py` — env 로드
- [ ] `app/db/base.py`, `app/db/models.py` — SQLAlchemy 모델 ([[../spec/database]])
- [ ] Alembic 초기화 + 첫 마이그레이션 ([[../spec/database#스키마]])
- [ ] `app/main.py` — FastAPI 앱, startup에서 마이그레이션 실행 ([[../spec/backend-api#마이그레이션-운영]])
- [ ] `GET /health` 엔드포인트
- [ ] `scripts/create_admin.py` ([[../spec/database#시드-데이터]])

**Deliverable:** `uvicorn app.main:app` → `curl localhost:8000/health` 200, DB에 admin 1명.

---

## Phase 2 — 인증 (admin 로그인)
**Goal:** 비밀번호로 JWT 발급 + 보호된 엔드포인트 검증

- [ ] `app/core/security.py` — 비밀번호 해싱, JWT 처리 ([[../domain/user#인증]])
- [ ] `app/core/deps.py` — `current_user` / `agent_auth` 의존성 ([[../spec/backend-api#인증]])
- [ ] `POST /api/auth/login`, `GET /api/auth/me` ([[../spec/backend-api#auth]])
- [ ] CORS 미들웨어 ([[../spec/backend-api#cors]])

**Deliverable:** `curl -X POST .../login` → JWT, `curl -H "Authorization: Bearer ..." .../me` → 본인 정보.

---

## Phase 3 — 사용자 / 카드 CRUD (스캔 제외)
**Goal:** 카드 등록만 빼고 나머지 데이터 조작 다 됨

- [ ] `GET/POST/PATCH /api/users` ([[../spec/backend-api#users]])
- [ ] `GET/POST/PATCH /api/cards` (UID 정규화 헬퍼 포함, `cards/scan` 제외)
- [ ] UID UNIQUE 충돌 시 409 응답

**Deliverable:** API로 사용자 추가, UID 직접 입력해서 카드 등록 가능.

---

## Phase 4 — 등록 리더(#2) 연동
**Goal:** `POST /api/cards/scan`이 실제로 카드 읽음

- [ ] `app/services/card_reader.py` — pyscard 래퍼 ([[../spec/backend-api#등록-리더2-운영]])
- [ ] `POST /api/cards/scan` 엔드포인트 ([[../spec/backend-api#post-apicardsscan-등록-리더2-on-demand-pull]])
- [ ] **macOS dev에서 ACR122U로 직접 테스트** (이미 `nfc-list` 동작 확인됨)

**Deliverable:** `curl -X POST .../cards/scan` → 카드 찍으면 UID 반환.

---

## Phase 5 — 출입 엔드포인트
**Goal:** Pi 에이전트가 보낼 인터페이스 완성

- [ ] `POST /api/access` (X-Agent-Key 인증, [[../spec/backend-api#access]])
- [ ] `access_logs` insert (allowed/denied 모두)
- [ ] cards/users 조회로 allowed 판정

**Deliverable:** `curl -X POST -H "X-Agent-Key: ..." .../access` → DB에 로그 + allowed 응답.

---

## Phase 6 — NFC 에이전트
**Goal:** 카드 태그하면 백엔드로 push 가는 단순 데몬

- [ ] `agent/` Python 프로젝트
- [ ] `nfc_agent/reader.py` — 출입용 리더 감시 (CardRequest 블로킹)
- [ ] `nfc_agent/client.py` — httpx로 `POST /api/access`
- [ ] `nfc_agent/feedback.py` — ACR122U PSEUDO-APDU 비프/LED
- [ ] `nfc_agent/main.py` — 메인 루프 ([[../spec/nfc-agent#메인-루프-의사-코드]])
- [ ] **macOS에서 직접 실행 + 백엔드 호출 확인** (Pi 가기 전에 다 검증)

**Deliverable:** 로컬에서 `python -m nfc_agent` → 카드 찍으면 백엔드에 로그 쌓임 + 비프음.

---

## Phase 7 — Logs / Stats API
**Goal:** 관리자 웹에서 보여줄 데이터 다 준비됨

- [ ] `GET /api/logs` ([[../spec/backend-api#logs]])
- [ ] `GET /api/stats/daily`, `GET /api/stats/monthly` ([[../spec/backend-api#stats]], 해석 규칙은 [[../domain/access-log#출퇴근-해석]])

**Deliverable:** API로 로그 조회 + 일/월별 출퇴근 통계 반환.

---

## Phase 8 — 관리자 웹 스켈레톤 + 인증
**Goal:** Next.js 앱에서 로그인 → 토큰 → 보호된 라우트 진입

- [ ] `admin/` Next.js 초기화 ([[../spec/admin-web#ui--차트]] 따라 UI 라이브러리 셋업)
- [ ] `lib/api.ts` — HTTP 클라이언트 ([[../spec/admin-web#데이터-페칭]])
- [ ] `app/login/page.tsx` ([[../spec/admin-web#login]])
- [ ] 인증 가드 ([[../spec/admin-web#인증--권한]])

**Deliverable:** localhost:3000에서 로그인 → 토큰 받아 저장.

---

## Phase 9 — 관리자 웹 페이지
**Goal:** 5개 페이지 다 동작

- [ ] `/logs` — 출입 로그 표 + 필터 + 페이지네이션
- [ ] `/users` — 사용자 목록 + 추가 + active 토글
- [ ] `/users/[id]` — 사용자 상세 + 카드 등록 (scan → UID 받기 → 저장)
- [ ] `/stats` — 일별/월별 표

**Deliverable:** 로컬에서 풀 워크플로 가능 — 로그인 → 사용자 추가 → 카드 등록(등록 리더) → 카드 태그(출입 리더) → 로그 확인.

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
