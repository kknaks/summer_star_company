# Python Convention

적용 범위: `backend/` (FastAPI), `agent/` (NFC 에이전트). 둘 다 Python.

공통 규칙은 [[common]] 참조.

## 스타일

- **포매터/린터**: ruff (lint + format) — `pyproject.toml`에 설정
- **타입힌트 필수** — 모든 public 함수 시그니처. mypy까지는 안 강제 (1인 스코프)
- 함수/변수: `snake_case`
- 클래스: `PascalCase`
- 상수: `UPPER_SNAKE_CASE`
- 라인 길이: 100자 (기본 ruff)
- 비공개는 `_prefix`

## 임포트 순서

```python
# 1. 표준 라이브러리
import asyncio
from datetime import datetime

# 2. 서드파티
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

# 3. 로컬
from app.core.config import settings
from app.db.models import User
```

ruff `isort` 자동 정렬.

## 백엔드 레이어 구조 (`backend/`)

**요청 흐름:**
```
HTTP 요청
  → schema (Pydantic in)        # 입력 검증
  → router (APIRouter)           # 엔드포인트 dispatch
  → dto (in)                     # 내부 전달용 객체
  → service                      # 비즈니스 로직
  → repo                         # DB 추상화
  → db (SQLAlchemy ORM)          # 실제 쿼리
  ← dto (out)                    # 결과 전달
  ← service (조립/검증)
  ← schema (Pydantic out)        # 응답 직렬화
HTTP 응답
```

### 디렉토리 매핑

```
backend/app/
├── api/               # router 계층
│   ├── auth.py
│   ├── users.py
│   ├── cards.py
│   ├── access.py
│   ├── logs.py
│   └── stats.py
├── schemas/           # Pydantic in/out
│   ├── auth.py
│   ├── users.py
│   └── ...
├── dtos/              # 내부 DTO (서비스 ↔ 레포)
│   ├── users.py
│   └── ...
├── services/          # 비즈니스 로직
│   ├── auth_service.py
│   ├── user_service.py
│   ├── card_service.py
│   └── card_reader.py    # pyscard 등록 리더
├── repos/             # DB 접근 계층
│   ├── user_repo.py
│   ├── card_repo.py
│   └── access_log_repo.py
├── db/
│   ├── base.py         # engine, sessionmaker
│   └── models.py       # SQLAlchemy ORM
├── core/
│   ├── config.py       # pydantic-settings
│   ├── security.py     # bcrypt, JWT
│   └── deps.py         # FastAPI Depends
└── main.py
```

### 레이어 규칙 (위→아래만 호출)

| 레이어 | 호출 가능 | 금지 |
|---|---|---|
| `api/` (router) | `services/`, `schemas/`, `core/deps` | 직접 `repos/`, `db/` |
| `services/` | `repos/`, `dtos/`, 다른 `services/` | `schemas/` import, FastAPI 의존 |
| `repos/` | `db/models`, `dtos/` | `services/`, `schemas/`, FastAPI |
| `db/` | (외부 호출 없음, ORM 모델만) | — |

핵심:
- **router는 service만 호출**. 직접 ORM/Session 만지지 않음
- **service는 schema 모름** — 내부 DTO만 다룸. router가 schema↔DTO 변환
- **repo는 재사용 가능** — FastAPI 의존성/Pydantic 무관, SQLAlchemy 세션만 받아 작동
- **schema vs dto** 구분 필요 — schema는 HTTP 경계, dto는 내부 전달

### schema ↔ dto 변환 위치

router에서 처리:
```python
# api/users.py
@router.post("/users")
async def create_user(
    payload: UserCreate,                      # schema (in)
    service: UserService = Depends(get_user_service),
):
    dto = UserCreateDTO(name=payload.name)    # schema → dto
    created: UserDTO = await service.create(dto)
    return UserResponse.model_validate(created)  # dto → schema (out)
```

> `model_validate`로 Pydantic이 dto 필드 자동 매핑.

## NFC 에이전트 (`agent/`)

레이어 분리는 가벼움 — 단순 데몬:
- `nfc_agent/main.py` — 메인 루프
- `nfc_agent/reader.py` — pyscard 래퍼
- `nfc_agent/client.py` — httpx 백엔드 클라
- `nfc_agent/feedback.py` — APDU 비프/LED
- `nfc_agent/config.py` — 환경변수

엄격한 레이어 룰 X. 단방향 의존만 지키면 됨 (`main → reader/client/feedback`).

## 비동기

- 백엔드는 **모두 async** — DB 세션은 `AsyncSession`, 핸들러도 `async def`
- 에이전트는 **sync 우선** — pyscard가 블로킹 호출. asyncio 도입 X (단순함 우선)

## 에러 처리

- HTTP 4xx는 `HTTPException`으로 raise (router/service에서 둘 다 OK)
- 5xx는 raise하지 말고 unhandled exception → FastAPI가 500 변환 + 로그
- 도메인 에러는 사용자 정의 예외 클래스 (`UserNotFound`, `CardConflict` 등) → router에서 HTTPException 변환
- 빈 try/except 금지

## 의존성 주입 (FastAPI)

- DB 세션: `Depends(get_session)` — `core/deps.py`
- 인증: `Depends(current_user)` (JWT) / `Depends(agent_auth)` (X-Agent-Key)
- 서비스: `Depends(get_user_service)` 등 — repo도 같은 방식

## 마이그레이션

- 모든 스키마 변경 = Alembic 마이그레이션
- DB 직접 수정 금지
- 마이그레이션은 startup 시 자동 적용 ([[../spec/backend-api#마이그레이션-운영]])

## 참고

- [[common]] — 언어 무관 공통
- [[../spec/backend-api]] — 엔드포인트 / 인증
- [[../spec/database]] — DB 스키마
- [[../spec/nfc-agent]] — 에이전트 구조
