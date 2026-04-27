# TypeScript Convention

적용 범위: `admin/` (Next.js 관리자 웹).

공통 규칙은 [[common]] 참조.

## 스타일

- **포매터**: prettier
- **린터**: eslint (`next/core-web-vitals` 베이스)
- **TypeScript strict 모드 ON** — `strict: true`, `noImplicitAny`
- 컴포넌트 파일: `PascalCase.tsx` (예: `UserTable.tsx`)
- 훅 파일: `camelCase.ts` (예: `useUsers.ts`)
- 라우트 파일: Next.js 규약 (`page.tsx`, `layout.tsx`, `loading.tsx`)
- 라우트 폴더: `kebab-case` (예: `app/access-logs/`)
- 변수/함수: `camelCase`
- 타입/컴포넌트: `PascalCase`
- 상수: `UPPER_SNAKE_CASE`

## 임포트 순서

```typescript
// 1. 외부
import { useState } from "react";
import axios from "axios";

// 2. 내부 절대 경로 (~/ 또는 @/)
import { Button } from "@/components/ui/button";
import { useUsers } from "@/hooks/useUsers";

// 3. 상대 경로
import { formatDate } from "./utils";
```

prettier-plugin import 정렬 또는 eslint `import/order`.

## 프론트엔드 레이어 구조 (`admin/`)

**데이터 흐름:**
```
페이지 (app/...)
  → 컴포넌트 (UI, 표시 전용)
  → 훅 (useXxx, 상태/페칭 로직)
  → API 클라이언트 (lib/api/*)
  → axios (interceptor 토큰 부착)
  → 백엔드
```

### 디렉토리 매핑

```
admin/
├── app/                    # Next.js App Router (페이지/레이아웃)
│   ├── layout.tsx
│   ├── login/page.tsx
│   ├── logs/page.tsx
│   ├── users/
│   │   ├── page.tsx
│   │   └── [id]/page.tsx
│   └── stats/page.tsx
├── components/             # UI 컴포넌트 (shadcn/ui + 자체)
│   ├── ui/                 # shadcn/ui 생성물
│   └── (도메인별 컴포넌트, 예: UserTable, CardForm)
├── hooks/                  # 커스텀 훅
│   ├── useAuth.ts
│   ├── useUsers.ts
│   └── ...
├── lib/
│   ├── api/                # 타입 있는 API 함수
│   │   ├── client.ts       # axios 인스턴스 + interceptor
│   │   ├── auth.ts         # login, me
│   │   ├── users.ts        # listUsers, createUser, ...
│   │   ├── cards.ts
│   │   └── ...
│   ├── types/              # 백엔드 schema와 매칭되는 TS 타입
│   │   ├── user.ts
│   │   ├── card.ts
│   │   └── access-log.ts
│   └── utils/              # 일반 유틸 (formatDate 등)
└── public/
```

### 레이어 규칙 (위→아래만 호출)

| 레이어 | 호출 가능 | 금지 |
|---|---|---|
| `app/` (page) | `components/`, `hooks/` | `lib/api` 직접, `axios` 직접 |
| `components/` | `hooks/`, 다른 `components/` | `lib/api` 직접, `axios` |
| `hooks/` | `lib/api/*`, `lib/types`, `lib/utils` | `axios` 직접 |
| `lib/api/` | `client.ts` (axios 인스턴스), `lib/types` | React 훅, 컴포넌트 |
| `lib/types/` | (외부 의존 없음) | — |

핵심:
- **컴포넌트는 API 호출 X** — 훅을 통해서만 데이터 받기
- **훅은 axios 직접 호출 X** — `lib/api/*`의 타입 있는 함수만
- **`lib/api/*`만 axios 사용** — interceptor 한 곳에서 관리
- 표시 컴포넌트는 props만 받아 렌더링 (presentational), 상태/페칭은 페이지나 훅 레벨에서

### `lib/types/` ↔ 백엔드 스키마

- 백엔드 Pydantic schema와 1:1 대응 타입을 수동 작성
- 향후 OpenAPI 코드젠 도입 가능 (지금은 1인 스코프라 수동)
- 백엔드 schema 변경 시 반드시 여기도 업데이트

## React 패턴

- **함수 컴포넌트 only** (클래스 X)
- **`'use client'` 최소화** — 기본은 Server Component, 인터랙션 필요한 곳만 client
  - 단 `localStorage` 접근 필요한 인증 페이지는 client
- props는 인터페이스로 명시:
  ```typescript
  interface UserTableProps {
    users: User[];
    onEdit: (id: string) => void;
  }
  ```
- 컴포넌트 한 파일 한 export (default export 우선)

## 상태 관리

- **로컬**: `useState` / `useReducer`
- **서버 상태**: 커스텀 훅 (`useUsers` 등) 안에서 `useEffect` + `useState` 또는 향후 SWR/TanStack Query 도입
- **글로벌**: 일단 없음. JWT 토큰만 localStorage. 필요해지면 React Context

## 에러 처리

- API 에러는 `lib/api/client.ts` interceptor에서 일괄:
  - 401 → 토큰 제거 + `/login` 리다이렉트
  - 5xx → toast 알림 (또는 console)
- 컴포넌트는 `try/catch` 또는 react-hook-form 에러 핸들링

## UI 라이브러리

- **shadcn/ui + Tailwind** ([[../spec/admin-web#ui--차트]])
- shadcn 컴포넌트는 `components/ui/`에 생성
- 자체 컴포넌트는 `components/` 직하 또는 도메인 폴더

## 참고

- [[common]]
- [[../spec/admin-web]]
- [[../spec/backend-api]] — 호출할 API 명세
