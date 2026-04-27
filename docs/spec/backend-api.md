# Backend API Spec

FastAPI 기반. 집 서버에서 동작. SSOT는 다음 영역:
- HTTP 인터페이스(엔드포인트, 요청/응답 스키마)
- 인증 미들웨어
- 등록 리더(#2) 연동
- 환경설정 / CORS

도메인 규칙, DB 스키마는 각 owner 문서 참조.

## 기술 스택

- **FastAPI** + Uvicorn
- **SQLAlchemy 2.x async** + `asyncpg` ([[database]])
- **Alembic** 마이그레이션
- **passlib[bcrypt]** 비밀번호 해싱
- **PyJWT** (HS256)
- **pyscard** 등록 리더(#2) 직접 제어
- **Pydantic v2** 요청/응답 스키마
- **표준 `logging`** — 별도 옵저버빌리티 도입 X

## 베이스 URL

- 운영: `https://api.your-domain.com` (집 서버 Nginx → FastAPI)
- 로컬: `http://localhost:8000`

## 인증

[[../domain/user#인증]] SSOT. 두 가지 인증 메커니즘:

| 경로 | 방식 | 헤더 | 비고 |
|---|---|---|---|
| `/api/access` | API 키 | `X-Agent-Key: <key>` | Pi 에이전트만 호출 |
| 그 외 보호된 경로 | JWT Bearer | `Authorization: Bearer <jwt>` | `admin` role 검증 |
| `/api/auth/login` | 없음 | — | 공개 |

JWT payload: `{ sub: user_id, role: "admin", exp: <30days> }`. HS256, 시크릿은 `JWT_SECRET` 환경변수.

API 키는 환경변수 `AGENT_API_KEY`. 키 변경 시 Pi 설정도 같이 갱신.

## 엔드포인트

### Auth

#### `POST /api/auth/login`
공개. 비밀번호로 admin 로그인.
```
요청:  { "password": "..." }
응답:  { "token": "<jwt>", "user": { "id": "...", "name": "...", "role": "admin" } }
에러:  401 잘못된 비밀번호
```
> 1인 admin 스코프라 username 없음. 비밀번호만으로 식별.

#### `GET /api/auth/me`
JWT 검증 + 본인 정보 조회.
```
응답:  { "id": "...", "name": "...", "role": "admin" }
에러:  401 토큰 없음/만료/위조
```

---

### Users

모두 JWT 필요.

#### `GET /api/users`
전체 사용자 목록 (활성/비활성 모두).
```
응답:  [{ "id": "...", "name": "...", "role": "admin", "active": true, "card_count": 2, "last_access_at": "..." }, ...]
```

#### `POST /api/users`
사용자 추가. `role`은 일단 무시 (서버에서 기본값 할당).
```
요청:  { "name": "..." }
응답:  201 { "id": "...", "name": "...", ... }
```

#### `PATCH /api/users/{id}`
이름/활성 수정.
```
요청:  { "name"?: "...", "active"?: bool }
응답:  200 { ... }
```

> 하드 삭제 엔드포인트 없음. soft delete는 `active=false`로 PATCH ([[../domain/user]]).

---

### Cards

모두 JWT 필요.

#### `POST /api/cards/scan` ⭐ 등록 리더(#2) on-demand pull
[[../domain/card#등록-흐름]]. 백엔드가 등록 리더에서 카드 한 장 읽고 UID 반환. **DB 쓰기 없음**.
```
요청:  (body 없음)
응답:  200 { "uid": "59FAC303" }
에러:  408 timeout (30초 내 카드 안 찍힘)
       503 reader_unavailable (#2 리더 분리/장애)
```
- pyscard로 등록 리더에 직접 connect, `asyncio.wait_for(timeout=30)`
- UID 정규화 (대문자 hex, 구분자 제거) 후 응답 ([[../domain/card]])
- 동시에 여러 admin이 호출하면? — 1인 운영이라 무시 (락 안 걸음)

#### `GET /api/cards?user_id={uuid}`
사용자별 카드 목록. `user_id` 없으면 전체.
```
응답:  [{ "id": "...", "uid": "59FAC303", "user_id": "...", "label": "메인", "active": true, "registered_at": "..." }, ...]
```

#### `POST /api/cards`
카드 등록 저장.
```
요청:  { "uid": "59FAC303", "user_id": "...", "label"?: "..." }
응답:  201 { ... }
에러:  409 conflict (UID 중복)
       404 user_id 없음
```
- 입력 UID 정규화 → UNIQUE 검사 → INSERT

#### `PATCH /api/cards/{id}`
라벨/활성 수정.
```
요청:  { "label"?: "...", "active"?: bool }
```

---

### Access (Pi 에이전트 push)

#### `POST /api/access` ⭐ API 키 인증
[[../domain/access-log]] SSOT. Pi 에이전트가 카드 태그될 때마다 호출.
```
요청 헤더: X-Agent-Key: <agent-key>
요청 body:
  {
    "uid": "59FAC303",
    "occurred_at": "2026-04-27T09:30:00+09:00"
  }
응답: 200 { "allowed": true | false }
에러: 401 잘못된 API 키
      422 잘못된 페이로드
```

처리 로직:
1. UID 정규화
2. `cards` 조회 (UID + active=true) → 없으면 `allowed=false`
3. `users.active=true` 추가 검증 → 비활성이면 `allowed=false`
4. `access_logs` INSERT (성공/실패 모두)
5. `received_at`은 서버 NOW()

> `occurred_at`은 클라가 보낸 값을 신뢰, `received_at`은 서버 시각. 보통 두 값이 거의 동일.

---

### Logs

JWT 필요.

#### `GET /api/logs`
출입 로그 조회. 필터/페이지네이션.
```
쿼리: ?user_id=&from=&to=&allowed=&limit=50&cursor=...
응답: { "items": [...], "next_cursor": "..." }
```
- 정렬: `occurred_at DESC, id DESC`
- **cursor pagination** (offset 안 씀 — 로그 누적되면 deep offset 비용 ↑). 커서 = 마지막 row의 `(occurred_at, id)` base64 인코딩

---

### Stats

JWT 필요. 출/퇴근 해석 규칙은 [[../domain/access-log#출퇴근-해석]] (KST 04:00 컷오프).

#### `GET /api/stats/daily?user_id=...&year=...&month=...`
일별 출/퇴근 (한 달치).
```
응답: [
  { "date": "2026-04-27", "first_in": "09:12", "last_out": "18:45", "duration_minutes": 573 },
  ...
]
```

#### `GET /api/stats/monthly?user_id=...&year=...`
월별 집계.
```
응답: [
  { "month": "2026-04", "work_days": 21, "avg_first_in": "09:08", "avg_last_out": "18:50", "avg_duration_minutes": 580 },
  ...
]
```

> 통계는 SQL로 계산 (백엔드 메모리에 끌어다 처리하지 말 것). KST 컷오프는 `(occurred_at - INTERVAL '4 hours') AT TIME ZONE 'Asia/Seoul'` 같은 식으로 처리.

---

## 공통 응답 / 에러

- 모든 응답 JSON
- 에러 포맷: `{ "detail": "<message>" }` (FastAPI 기본)
- 422 — Pydantic 검증 실패 (자동)
- 5xx — 서버 에러, 로그 남김

## CORS

Vercel admin 웹이 cross-origin 호출. CORSMiddleware:
- `allow_origins`: `["https://<vercel-domain>", "http://localhost:3000"]`
- `allow_methods`: `["GET", "POST", "PATCH", "OPTIONS"]`
- `allow_headers`: `["Authorization", "Content-Type"]`
- `allow_credentials`: False (Bearer 토큰이라 쿠키 불필요)

## 환경 변수

| 변수 | 설명 |
|---|---|
| `DATABASE_URL` | postgres async URL (`postgresql+asyncpg://...`) |
| `JWT_SECRET` | JWT 서명 시크릿 (32바이트 이상 랜덤) |
| `AGENT_API_KEY` | Pi 에이전트 인증 키 |
| `CORS_ORIGINS` | 콤마 구분 origin 목록 |
| `READER_NAME` | pyscard에서 잡을 등록 리더 이름 (`ACS ACR122U PICC Interface` 등) |
| `READER_TIMEOUT_SEC` | scan timeout (default 30) |

## 등록 리더(#2) 운영

- pyscard로 직접 제어 — Docker 사용 시 USB 디바이스 passthrough 필요 (`--device=/dev/bus/usb/...` 또는 host network + udev 규칙)
- macOS는 PC/SC 데몬이 가끔 USB를 잡고 안 놓는 이슈 있음 → 발생 시 `sudo killall -9 pcscd` 후 재시도
- 동일 시점에 두 admin이 동시 scan 호출하면 한쪽은 reader busy. 1인 운영이라 무시

## 프로젝트 구조 (제안)

```
backend/
├── app/
│   ├── main.py              # FastAPI 앱 + 미들웨어 + 라우터 등록
│   ├── api/
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── cards.py
│   │   ├── access.py
│   │   ├── logs.py
│   │   └── stats.py
│   ├── core/
│   │   ├── config.py        # pydantic-settings
│   │   ├── security.py      # bcrypt, JWT
│   │   └── deps.py          # 인증 deps (current_user, agent_auth)
│   ├── db/
│   │   ├── base.py          # async engine, sessionmaker
│   │   └── models.py        # SQLAlchemy
│   ├── schemas/             # Pydantic
│   └── services/
│       └── card_reader.py   # pyscard 래퍼
├── alembic/
└── scripts/
    └── create_admin.py      # 초기 admin 시드 ([[database#시드-데이터]])
```

## 마이그레이션 운영

**자동 실행** — 앱 시작 시 `alembic upgrade head`. 실패하면 앱이 아예 안 뜸 (= 깨진 상태로 트래픽 받지 않음).
- `app/main.py`의 startup 단계에서 실행
- 운영 중 로컬 DB 직접 수정 금지 — 무조건 마이그레이션 파일로
- 위험한 마이그레이션(데이터 변형, 다운타임)은 수동 적용 후 자동 단계는 no-op이 되도록 작업

## 참고

- [[../architecture/overview]]
- 도메인: [[../domain/user]] / [[../domain/card]] / [[../domain/access-log]]
- DB: [[database]]
- 사용처: [[admin-web]] / [[nfc-agent]]
