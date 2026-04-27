# Repo Layout

**결정: 단일 monorepo.**

## 이유

- 1인 프로젝트 + 3개 컴포넌트(backend / agent / admin)가 같이 진화 → 폴리레포 동기화 오버헤드만 추가됨
- 도메인 결정이 바뀌면 backend/agent/admin이 같이 따라가야 함 → 한 PR/커밋으로 묶어야 정합 유지
- backend와 agent는 둘 다 Python — UID 정규화 같은 공통 함수가 필요해지면 `shared/` 폴더로 빼기 쉬움
- Vercel은 monorepo Root Directory 설정 지원 (`admin/`만 빌드)

## 디렉토리 트리

```
summer_star_company/
├── CLAUDE.md                    # Claude Code 진입점
├── docs/                        # 모든 문서 ([[../MAP]])
├── .claude/                     # agents / skills / hooks / commands
│
├── backend/                     # FastAPI (집 서버 배포)
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── schemas/
│   │   └── services/
│   ├── alembic/
│   ├── scripts/                 # create_admin.py 등
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
│
├── agent/                       # Pi 에이전트 (Pi 배포)
│   ├── nfc_agent/
│   │   ├── main.py
│   │   ├── reader.py
│   │   ├── client.py
│   │   ├── cache.py
│   │   ├── queue.py
│   │   ├── feedback.py
│   │   └── config.py
│   ├── systemd/
│   │   └── nfc-agent.service
│   ├── tests/
│   └── pyproject.toml
│
├── admin/                       # Next.js (Vercel 배포)
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── package.json
│   └── next.config.js
│
├── docker-compose.yml           # 로컬 dev: postgres + backend
├── .gitignore
└── .env.example                 # 시크릿 템플릿 ([[security]])
```

## 컴포넌트 의존 / 빌드

- **backend** ↔ **agent**: 직접 import 없음, HTTP로만 통신. 공통 코드 필요해지면 `shared/` 신설
- **admin**: 백엔드와 HTTP만. 타입 공유 필요 없으면 굳이 backend 의존성 X
- **테스트**: 각 컴포넌트별로 독립 (`backend/tests/`, `agent/tests/`)

## Vercel monorepo 셋업

- Vercel 프로젝트 생성 시 Root Directory: `admin/`
- 빌드 명령: `next build`
- `admin/` 외의 변경은 admin 빌드 트리거 안 시키도록 ignored build step 설정

## 공통 코드 (`shared/`) — 지금은 안 만듦

backend와 agent가 둘 다 Python이지만 지금은 각자 작은 정규화 함수 정도라 중복이 적음. 나중에 동일 로직 두 군데 넘으면 그때 `shared/` 만들기.

## 참고

- [[overview]] — 컴포넌트 배포 위치
- [[security]] — `.env` 관리
- [[../MAP]] — 문서 인덱스
