# Database Spec

Postgres 스키마, 마이그레이션, 인덱스 SSOT. 도메인 의미는 [[../domain/user]] / [[../domain/card]] / [[../domain/access-log]] 참조.

## 호스팅 / 도구

- **DB**: 집 서버의 자호스팅 Postgres (FastAPI도 같은 박스, [[../architecture/overview]] 참조)
- **로컬 개발**: Docker Compose로 Postgres 17 컨테이너
- **마이그레이션**: Alembic (확정)
- **ORM**: SQLAlchemy 2.x async + `asyncpg` 드라이버 (확정)
- **백업**: 매일 `cron`으로 `pg_dump` → 외장 스토리지 (디테일은 [[../architecture/security]] 또는 별도 운영 문서)

## 스키마

### `users`

[[../domain/user]] SSOT. 이 표는 SQL 매핑.

```sql
CREATE TYPE user_role AS ENUM ('admin');  -- 향후 'member', 'guest' 추가 시 ALTER TYPE

CREATE TABLE users (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name          TEXT NOT NULL,
  role          user_role NOT NULL DEFAULT 'admin',
  password_hash TEXT,                                           -- admin만 채워짐 (passlib bcrypt)
  active        BOOLEAN NOT NULL DEFAULT TRUE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

비고:
- `password_hash`는 nullable — 직원(향후 member role) 추가 시 비밀번호 없이 카드만 쓰는 경우 대응
- `id` UUID v4 (gen_random_uuid는 pgcrypto 또는 PG13+ 내장)

### `cards`

[[../domain/card]] SSOT.

```sql
CREATE TABLE cards (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  uid            TEXT UNIQUE NOT NULL,                         -- 정규화 규칙은 domain/card 참조
  user_id        UUID NOT NULL REFERENCES users(id),
  label          TEXT,
  active         BOOLEAN NOT NULL DEFAULT TRUE,
  registered_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX cards_user_id_idx ON cards(user_id);
CREATE INDEX cards_active_idx  ON cards(active) WHERE active = TRUE;  -- 부분 인덱스
```

비고:
- `uid` UNIQUE — 같은 카드 중복 등록 차단
- 정규화는 **앱 레이어에서** 강제 (DB CHECK 안 둠 — 정규식 유지보수 비용 ↑). 자세한 규칙은 [[../domain/card]]
- `ON DELETE` 정책: `user_id`는 RESTRICT (사용자 삭제 시 카드 정리부터 강제)

### `access_logs`

[[../domain/access-log]] SSOT.

```sql
CREATE TABLE access_logs (
  id           BIGSERIAL PRIMARY KEY,
  occurred_at  TIMESTAMPTZ NOT NULL,                           -- Pi에서 카드 찍힌 시각
  received_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),             -- 백엔드 수신 시각
  uid          TEXT NOT NULL,                                  -- 미등록 카드도 raw 보존
  card_id      UUID REFERENCES cards(id),                      -- NULL 허용
  user_id      UUID REFERENCES users(id),                      -- NULL 허용
  allowed      BOOLEAN NOT NULL
);

CREATE INDEX access_logs_occurred_at_idx       ON access_logs(occurred_at DESC);
CREATE INDEX access_logs_user_id_occurred_idx  ON access_logs(user_id, occurred_at DESC);
CREATE INDEX access_logs_uid_occurred_idx      ON access_logs(uid, occurred_at DESC);
```

비고:
- BIGSERIAL — UUID보다 시간순 정렬/페이징에 유리
- `card_id` / `user_id` ON DELETE: SET NULL (삭제돼도 로그 보존). 단 도메인상 카드/유저는 soft delete가 원칙이라 이 경로는 사실상 안 탐
- 통계 뷰 안 만듦 — 출/퇴근 해석은 앱 레이어 ([[../domain/access-log#출퇴근-해석]])

## 트리거 / 자동화

- `updated_at` 자동 갱신: 트리거로 `BEFORE UPDATE` 처리 (users, cards 두 테이블)

```sql
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_set_updated_at BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER cards_set_updated_at BEFORE UPDATE ON cards
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

## 마이그레이션 운영

- 마이그레이션 파일: `backend/alembic/versions/*.py` (백엔드 레포 안)
- 로컬: `alembic upgrade head`
- 운영: 배포 파이프라인의 일부로 실행 (백엔드 컨테이너 부팅 시 자동 적용 X — 명시적으로)

## 시드 데이터

- 초기 admin 계정 생성용 스크립트 (CLI): `python -m backend.scripts.create_admin --name ... --password ...`
- 빈 DB → 마이그레이션 적용 → 시드 스크립트로 admin 1명 생성 → 끝

## 참고

- [[../architecture/overview]]
- 도메인: [[../domain/user]] / [[../domain/card]] / [[../domain/access-log]]
- 백엔드 사용처: [[backend-api]]
