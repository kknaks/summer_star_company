# NFC Agent Spec

라즈베리파이에서 상시 동작하는 Python 프로세스. 출입용 리더(#1)를 감시하고 백엔드로 카드 이벤트 push.

도메인 의미는 [[../domain/access-log]] / [[../domain/card]] 참조. 백엔드 인터페이스는 [[backend-api]] 참조.

## 책임

1. **카드 감시 루프** — 출입 리더에서 카드 태그 감지
2. **백엔드 push** — `POST /api/access`
3. **하드웨어 피드백** — 통과/거부 신호 (비프음, LED)

> 의도적으로 단순화: 로컬 캐시/큐/오프라인 폴백 없음. 네트워크 이슈로 실패하면 사용자가 다시 태그하면 됨. 1인 운영이라 이 트레이드오프가 합당.

## 기술 스택

- **Python 3.11+** (Pi 64bit OS 기준)
- **pyscard** — PC/SC 인터페이스 (등록 리더 백엔드와 동일 라이브러리)
- **httpx** — HTTP 클라이언트 (sync 모드 사용, async 전환 여지)
- **systemd** — 자동 시작/재시작

## 메인 루프 (의사 코드)

카드 감지는 **pyscard `CardRequest`** (블로킹). 단일 리더라 이벤트 모델(`CardMonitor`)까지 갈 필요 없음.

```python
def main():
    while True:
        uid = reader.wait_for_card()         # CardRequest, 블로킹
        occurred_at = now_utc_iso()
        uid = normalize(uid)                 # 대문자 hex, 구분자 제거

        try:
            response = client.post_access(uid, occurred_at)
            allowed = response["allowed"]
        except (NetworkError, BackendError) as e:
            log.warning("access push failed: %s", e)
            allowed = False                  # 실패 = 거부 (사용자 재태그)

        feedback.signal(allowed)
```

## 에러 처리

- **네트워크 실패 / 백엔드 에러 / timeout** → 거부 신호 + 에러 로그 → 사용자가 재태그
- **리더 분리/장애** → 짧은 sleep 후 reconnect 재시도 (systemd가 죽으면 살림)
- **로그**: 표준 logging → systemd journal (`journalctl -u nfc-agent`)
- 미전송 이벤트 보존하지 않음 (스코프 외 — [[#추후-고려]])

## 하드웨어 피드백

ACR122U 내장 기능으로 시작:
- **허용**: 짧은 비프 1회 + 그린 LED 1초
- **거부**: 긴 비프 1회 + 레드 LED 1초
- 명령: pyscard로 ACR122U PSEUDO-APDU 전송 (`FF 00 40 LL 04 t1 t2 r g`)

> GPIO로 외부 LED/부저 다는 건 결정 미뤄둠 (필요 생기면 추가).

## 환경 변수

| 변수 | 기본값 | 설명 |
|---|---|---|
| `API_BASE_URL` | — | 백엔드 베이스 (`https://api.your-domain.com`) |
| `AGENT_API_KEY` | — | `X-Agent-Key` 헤더 값 |
| `READER_NAME` | (auto-detect) | pyscard 리더 이름 일부 매칭 |
| `HTTP_TIMEOUT_SEC` | `5` | 백엔드 호출 타임아웃 |
| `LOG_LEVEL` | `INFO` | 표준 logging 레벨 |

## systemd 운영

`/etc/systemd/system/nfc-agent.service`:
```ini
[Unit]
Description=NFC Access Agent
After=network-online.target pcscd.service
Wants=network-online.target pcscd.service

[Service]
Type=simple
User=nfc
WorkingDirectory=/opt/nfc-agent
EnvironmentFile=/etc/nfc-agent.env
ExecStart=/opt/nfc-agent/.venv/bin/python -m nfc_agent
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

- `pcscd` 의존성 명시 — PC/SC 데몬 떠야 리더 잡힘
- 죽으면 5초 후 재시작 (`Restart=on-failure`)
- 환경변수는 별도 파일(`/etc/nfc-agent.env`, root만 읽기)

## 로깅

- 표준 `logging` 모듈, JSON 포맷 X
- 출력: stdout → systemd journal에 자동 수집
- 조회: `journalctl -u nfc-agent -f`

## 프로젝트 구조 (제안)

```
agent/
├── pyproject.toml
├── nfc_agent/
│   ├── __init__.py
│   ├── __main__.py        # python -m nfc_agent 진입점
│   ├── main.py            # 메인 루프
│   ├── reader.py          # pyscard 래퍼 (대기 + UID 추출 + APDU 피드백)
│   ├── client.py          # httpx 백엔드 클라이언트
│   ├── feedback.py        # 비프/LED
│   └── config.py          # pydantic-settings 또는 os.environ
├── systemd/
│   └── nfc-agent.service
└── tests/
```

## 추후 고려 (현 스코프 밖)

- **오프라인 캐시 / 미전송 큐** — 인터넷 자주 끊기는 환경 되면 추가. 현재는 "안 되면 재태그" 정책
- 외부 GPIO LED/부저 — 일단 ACR122U 내장 비프/LED로 충분
- Pi 장기 단절 시 admin 알림 — 현재는 침묵 동작

## 참고

- [[../architecture/overview]]
- 도메인: [[../domain/card]] / [[../domain/access-log]]
- 백엔드 인터페이스: [[backend-api]]
- 운영: [[../architecture/deployment-pi]] (실제 배포 시 작성)
