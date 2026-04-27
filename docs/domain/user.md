# User (사용자)

출입 권한을 가진 직원. 사람 한 명에 1:1 대응.

> **스코프 메모**: 개인 사무실용. 관리자 = 본인 1명, 등록되는 직원도 소수. SaaS/멀티테넌트 아님.

## 속성 (초안)

| 필드 | 타입 | 비고 |
|---|---|---|
| id | uuid | PK |
| name | text | 표시명 |
| role | enum | 일단 `admin`만. 향후 `member` / `guest` 등 확장 가능하도록 enum으로 둠 |
| active | bool | 비활성화 (퇴사 시 false) |
| created_at | timestamptz | |
| updated_at | timestamptz | |

> 이메일 필드는 일단 보류. 알림(슬랙/카톡 등) 기능 붙일 때 추가.

## 관계

- 1 [[user]] : N [[card]] — 한 사용자가 카드 여러 장 가능 (분실 대비 예비카드)
- 1 [[user]] : N [[access-log]] — 출입 기록의 주체

## 인증

- **관리자 웹**: 비밀번호 로그인 → JWT 발급 → 클라이언트 `localStorage` 저장 → 이후 요청은 `Authorization: Bearer <token>` 헤더
- **토큰 TTL**: 30일 (만료 시 재로그인)
- **JWT 시크릿**: 백엔드 환경변수 `JWT_SECRET` (HS256)
- **stateless** — DB에 sessions 테이블 없음. 강제 로그아웃은 시크릿 로테이션으로 일괄 처리
- **비밀번호 해싱**: `bcrypt` (직접 사용 — passlib는 bcrypt 4.x 호환 이슈로 회피)
- **Pi 에이전트 → 백엔드**: 정적 API 키 헤더 (`X-Agent-Key: ...`) — JWT 아님
- 일반 직원은 로그인 안 함 — 카드만 찍음 (role 추가되면 그때 재검토)

## 등록 흐름

1. admin이 [[../spec/admin-web]]에서 사용자 추가 (이름만)
2. 사용자 상세 페이지에서 카드 등록 (디테일은 [[card#등록-흐름]])
3. 끝

self-signup 없음. admin invite-only.

## 참고

- [[../architecture/overview|아키텍처 개요]]
- 백엔드 스펙: [[../spec/backend-api]]
- DB 스키마: [[../spec/database]]
