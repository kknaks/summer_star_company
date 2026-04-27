# Admin Web Spec

Vercel에 배포되는 Next.js 기반 관리자 대시보드. admin 1명만 사용.

## 배포

- **호스팅**: Vercel (free tier)
- **도메인**: Vercel 기본 도메인(`*.vercel.app`) 또는 추후 커스텀 (옵션)
- **API 엔드포인트**: 환경변수 `NEXT_PUBLIC_API_BASE_URL` (예: `https://api.your-domain.com`)
- 관리자 웹 ↔ API 는 cross-origin이지만 **localStorage + Bearer 토큰 방식이라 CORS만 허용하면 끝** (쿠키 정책 신경 X)

## 페이지 구성

### `/login`
- 비밀번호 한 줄 입력 → `POST /api/auth/login` → 응답의 JWT를 `localStorage`에 저장
- 토큰 있으면 `/logs`로 자동 리다이렉트

### `/logs` — 출근 기록 [기본 페이지]
- 최근 [[../domain/access-log]] 테이블 표시
- 컬럼: 시각(occurred_at, KST 표시), 사용자, 카드 라벨, 허용 여부
- 필터: 사용자별 / 날짜 범위 / 허용·거부
- 정렬 기본: occurred_at DESC, 페이지네이션 (예: 50건/페이지)

### `/stats` — 출퇴근 통계
- 출/퇴근 해석 규칙은 [[../domain/access-log#출퇴근-해석]] 따름 (KST 04:00 컷오프, 첫·마지막 찍힘)
- **일별 뷰**: 사용자 선택 → 한 달치 출근/퇴근 시각 + 체류시간 표
- **월별 뷰**: 출근일수 / 평균 출근·퇴근 시각 / 평균 체류시간
- 처리는 **앱 레이어 (이 페이지 또는 백엔드)** — DB 뷰 안 만듦

### `/users` — 사용자 관리
- 목록: 이름 / 활성 여부 / 카드 수 / 최근 출입 시각
- 추가: 이름만 입력 (role은 자동 `admin` 또는 향후 `member`)
- 수정: name, active 토글
- 삭제: soft delete (`active=false`) — 도메인 규칙은 [[../domain/user]]

### `/users/[id]` — 사용자 상세 + 카드 등록
- 사용자 정보 + 보유 카드 목록
- "카드 추가" 버튼 → `POST /api/cards/scan` (백엔드가 등록 리더 #2에서 카드 읽음, timeout 30초)
- 응답으로 UID 받으면 → 라벨 입력 → "저장" → `POST /api/cards { uid, user_id, label }`
- timeout 시 에러 토스트 + 재시도 버튼
- 카드 분실: 카드 행에서 active 토글 (`PATCH /api/cards/{id} { active: false }`)
- 등록 흐름 디테일은 [[../domain/card#등록-흐름]]
- **실시간성 X** — 폴링/SSE/WebSocket 안 씀, 단순 요청-응답 사이클

## 인증 / 권한

- `/login` 외 모든 페이지는 JWT 검증 필요
- 검증 실패(만료 포함) → `/login` 리다이렉트 + localStorage 토큰 제거
- 디테일은 [[../domain/user#인증]]

## 데이터 페칭

- **axios** + interceptor로 `Authorization: Bearer` 자동 부착, 401 받으면 localStorage 토큰 제거 + `/login` 리다이렉트
- 클라이언트 컴포넌트에서 직접 호출 (Server Components 안 씀 — 토큰이 localStorage에 있어 SSR 어려움)

## UI / 차트

- **shadcn/ui** + Tailwind 채택
- 통계는 일단 **표 only** (recharts 등 시각화는 추후 필요해지면 도입)

## 참고

- [[../architecture/overview]]
- 도메인: [[../domain/user]] / [[../domain/card]] / [[../domain/access-log]]
- API: [[backend-api]]
