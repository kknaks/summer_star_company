# Security

시크릿 관리 / 네트워크 보안 / 백업 SSOT.

## 시크릿 인벤토리

| 시크릿 | 용도 | 위치 |
|---|---|---|
| `JWT_SECRET` | JWT HS256 서명 | 집 서버 백엔드 환경변수 |
| `AGENT_API_KEY` | Pi → 백엔드 호출 인증 | 집 서버 백엔드 + Pi 양쪽 |
| `DATABASE_URL` | Postgres 접속 | 집 서버 백엔드 환경변수 |
| admin 비밀번호 (해시) | 관리자 로그인 | DB `users.password_hash` |
| Postgres 슈퍼유저 비밀번호 | DB 운영 | docker-compose `.env` |
| Cloudflare/도메인 API 토큰 (있으면) | DDNS / Let's Encrypt | 별도 관리 |

## 시크릿 보관 원칙

- 시크릿은 **절대 git에 커밋하지 않음** — `.env` 는 `.gitignore`. 템플릿은 `.env.example`만 커밋
- 운영용 `.env`는 집 서버에 직접 배치 (`/etc/nfc-agent.env`, `/srv/backend/.env` 등)
- 파일 권한 `600` (소유자 읽기만), 소유자는 해당 서비스 user
- Pi의 `/etc/nfc-agent.env`도 동일 — `nfc` 유저 소유 + `600`

## 시크릿 생성

랜덤 시크릿은 길고 예측 불가능하게:
```bash
# JWT_SECRET, AGENT_API_KEY 등 32바이트 랜덤
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 회전 정책

- **JWT_SECRET** 회전 = 모든 admin 토큰 즉시 무효화 → 강제 재로그인. 의심 상황 시 회전
- **AGENT_API_KEY** 회전 = 백엔드 + Pi 양쪽 동시 갱신 (Pi 재시작 필요). 분기/반기 1회 정도
- admin 비밀번호 변경: admin 웹의 비밀번호 변경 페이지 (스펙은 추후 [[../spec/admin-web]]에 추가)

## 네트워크 / HTTPS

- 외부 노출은 **HTTPS만** — 평문 HTTP 금지
- 기존 Nginx에 `api.your-domain.com` server block 추가, Let's Encrypt 인증서 사용 (이미 다른 서비스에서 운영 중인 같은 패턴 재사용)
- Postgres는 **공개 노출 X** — 집 서버 내부 통신만, 방화벽으로 5432 차단
- Pi → 백엔드는 공개 인터넷이지만 **API 키 + HTTPS** 조합으로 보호

## CORS

- 백엔드 CORS는 admin Vercel origin + 로컬 dev만 허용 ([[../spec/backend-api#cors]])
- Wildcard `*` 사용 X

## Rate Limiting

선택사항이지만 공개 노출 엔드포인트 보호용:
- Nginx `limit_req_zone` 으로 IP당 분당 N회 정도
- 특히 `/api/auth/login` 은 brute-force 대비 짧은 윈도우(예: 분당 5회)
- 1인 운영이라 일단 안 깔아도 죽진 않음. **stretch goal**

## 백업

- DB 매일 `pg_dump` → 외장 스토리지 (집 서버 외장 디스크 또는 NAS)
- cron 예시:
  ```bash
  0 4 * * * pg_dump -U postgres summer_star_company | gzip > /backup/db/$(date +\%F).sql.gz
  find /backup/db -name "*.sql.gz" -mtime +30 -delete
  ```
- 30일 보관, 그 이후 삭제
- 1회/월 정도 복원 테스트 (안 그러면 백업 깨져있을 수 있음)

## Pi 보안

- SSH 키 인증만 (비밀번호 로그인 비활성화)
- 가능하면 SSH 포트 외부 노출 X — Tailscale/내부망에서만 접근
- `nfc` 전용 유저로 에이전트 실행, root 금지
- `unattended-upgrades` 활성화 — 보안 패치 자동

## 감사 / 로그

- 백엔드: 표준 `logging` → systemd journal
- Pi 에이전트: 동일
- 1인 운영이라 별도 SIEM 없음. `journalctl` 직접 조회로 충분

## 추후 고려

- 비밀번호 변경 / 분실 복구 흐름 (admin 웹에 추가)
- 의심 출입 패턴 자동 감지 (예: 미등록 카드 반복 거부 시 알림)
- Rate limiting 적용
- 시크릿 매니저(Vault/Doppler 등) — 1인 운영이라 과함

## 참고

- [[overview]]
- [[../spec/backend-api]] — 환경변수 / CORS
- [[../spec/nfc-agent]] — 에이전트 측 시크릿
- [[../spec/database]] — DB 호스팅 / 백업
