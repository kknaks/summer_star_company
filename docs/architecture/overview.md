# 시스템 아키텍처 개요

NFC 카드 기반 출입 시스템. 4개 컴포넌트로 구성.

> **이 문서는 요약(summary)입니다.** 큰 그림과 컴포넌트 간 관계를 보여주는 진입점이며, 각 항목의 SSOT(상세 결정)는 링크된 도메인/스펙 문서입니다. 디테일이 필요하면 링크를 따라가세요.

> **스코프**: 본인 개인 사무실 출퇴근 트래킹용. 관리자 1명(본인) / 직원 소수 / 리더기 1대(Pi). 멀티테넌트/SaaS 아님.

## 컴포넌트 구성

```
[사무실]                                  [집 서버]                    [Vercel]
                                                                    [Next.js Admin]
[ACR122U #1]─USB─[Pi: Python Agent] ─HTTP─> [FastAPI Backend] ←HTTPS── (브라우저)
   (출입용)                                       │
                                              SQL│  USB
                                                 ▼  ▼
                                        [Postgres]  [ACR122U #2]
                                                       (등록용, on-demand)
```

리더기 2대 분리:
- **#1 출입용** — Pi 에이전트가 상시 감시, 카드 태그 시 백엔드로 push (`/api/access`)
- **#2 등록용** — 집 서버에 USB로 직결, 백엔드가 등록 요청 받으면 그 자리에서 pull (`/api/cards/scan`)

Pi ↔ 집 서버 도달은 도메인 + Nginx 리버스 프록시 (HTTPS). 시크릿/방화벽 디테일은 [[security]].

| 컴포넌트 | 역할 | 배포 위치 |
|---|---|---|
| [[../spec/nfc-agent]] | 출입용 리더(#1) 감시, UID 백엔드 push | Raspberry Pi (사무실) |
| [[../spec/backend-api]] | 출입 판정 / CRUD / 등록 리더(#2) on-demand pull | 집 서버 |
| [[../spec/database]] | 데이터 저장 (Postgres) | 집 서버 (자호스팅) |
| [[../spec/admin-web]] | 운영자 대시보드 | Vercel |

## 기술 스택 결정

- **에이전트**: Python + `pyscard` 또는 `nfcpy`
  - 이유: 사용자 친숙도, ARM(Pi) 호환, 라이브러리 성숙도
- **백엔드**: FastAPI
  - 이유: Python 통일, 타입 힌트로 스키마 명확
- **DB**: Postgres (집 서버 자호스팅, Docker)
  - 이유: 사용자가 이미 집에 PG 서버 운영 중. 별도 호스팅 비용 0.
- **프론트**: Next.js
  - 이유: 관리자 대시보드용으로 충분, SSR/Auth 편의

## 인증

OAuth/세션쿠키 안 씀 — 1인 운영 스코프라 가장 단순한 조합. 두 가지 인증 경로:

- **관리자 웹 로그인** (JWT 30일, localStorage) — 디테일은 [[../domain/user#인증]] (SSOT)
- **에이전트 → 백엔드** (정적 API 키) — 디테일은 [[security]] (SSOT, 작성 예정)

## 핵심 흐름

1. **카드 등록** — 운영자가 [[admin-web]]에서 사용자 추가 → 카드 찍어서 UID 매핑
2. **출입** — Pi 에이전트가 카드 감지 → 백엔드 `/access/check` 호출 → 허용/거부 응답 + 출입 로그 기록
3. **모니터링** — 관리자 웹에서 실시간 출입 로그 / 통계 확인

## 운영 고려사항

- [[repo-layout]] — monorepo 디렉토리 구조
- [[security]] — 시크릿 / HTTPS / 백업
- [[deployment-pi]] — Pi 셋업, systemd (실제 배포 시 작성)

## 도메인 모델

- [[user]] — 사용자 (관리자 1명 + 직원 소수)
- [[card]] — NFC 카드 (UID, 소유자, 활성 여부)
- [[access-log]] — 출입 기록 (성공/실패 포함)
- ~~[[reader]]~~ — 리더기 1대 전제라 별도 모델 불필요. 향후 다중 리더 시 추가 검토

## 관련 문서

- 스펙: [[../spec/]]
- 도메인: [[../domain/]]
- 계획: [[../plan/]]
