# Pi 배포 (NFC Agent)

Orange Pi Zero 3 (또는 라즈베리파이/유사 ARM 보드)에 NFC 에이전트를 배포하는 SSOT.

에이전트 동작/스펙은 [[../spec/nfc-agent]] 참조. 이 문서는 **운영 배포 절차** 만 다룬다.

---

## 사전 조건

- ssh 로 Pi 접속 가능 (키 인증 권장 — [[security#pi-보안]])
- 백엔드가 도달 가능한 주소 하나 — 임시 LAN IP (`http://192.168.x.x:48000`) 또는 운영 도메인 (`https://ssc-api.kknaks.cloud`)
- `AGENT_API_KEY` 값 — 홈서버 backend `.env` 와 **동일한 문자열** ([[security#시크릿-인벤토리]])
- ACR122U USB 리더

---

## 1. 시스템 패키지

```bash
sudo apt update
sudo apt install -y git pcscd pcsc-tools libpcsclite-dev libccid libacsccid1 swig python3-dev curl
```

| 패키지 | 용도 |
|---|---|
| `pcscd` | PC/SC 데몬 — 리더 접근 |
| `pcsc-tools` | `pcsc_scan` 포함 (다음 단계 인식 확인) |
| `libccid`, `libacsccid1` | ACR122U/CCID 리더 드라이버 (Ubuntu Noble 은 자동 설치 안 됨 — 빠지면 `LIBUSB_ERROR_TIMEOUT`) |
| `libpcsclite-dev`, `swig`, `python3-dev` | pyscard 컴파일에 필요 |
| `git`, `curl` | 코드 클론 + uv 설치 |

---

## 2. 커널 모듈 블랙리스트

리눅스 NFC 커널 모듈(`pn533`/`nfc`)이 USB 리더를 먼저 잡으면 pcscd 가 리더를 못 본다. 차단:

```bash
sudo tee /etc/modprobe.d/blacklist-nfc.conf <<EOF
blacklist pn533
blacklist pn533_usb
blacklist nfc
EOF
sudo reboot
```

> 이 단계 빼먹으면 **코드는 멀쩡한데 카드만 안 잡혀서** 디버깅 시간 쓰기 쉬움.

---

## 3. 리더 인식 확인

재부팅 후 ssh 재접속:

```bash
pcsc_scan
```

- ACR122U 가 보이고, 카드 올리면 ATR 출력 → 정상. Ctrl+C 로 종료.
- 안 보이면 → [트러블슈팅](#트러블슈팅).

---

## 4. uv 설치

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

---

## 5. 코드 클론

```bash
sudo mkdir -p /opt && sudo chown "$USER" /opt
git clone https://github.com/kknaks/summer_star_company.git /opt/summer_star_company 
cd /opt/summer_star_company/agent
uv sync
```

---

## 6. 환경변수

시크릿이라 `/etc/` 에 두고 `root:$USER 640` — root 만 쓰기, 에이전트 user 읽기 (foreground 검증 시 `source` 가능해야 함):

```bash
sudo tee /etc/nfc-agent.env <<'EOF'
API_BASE_URL=https://ssc-api.kknaks.cloud
AGENT_API_KEY=changeme-please-generate-32-bytes
READER_NAME=ACR122U
HTTP_TIMEOUT_SEC=5
LOG_LEVEL=INFO
EOF
sudo chown "root:$USER" /etc/nfc-agent.env
sudo chmod 640 /etc/nfc-agent.env
```

> systemd 단계에서 user 를 `nfc` 로 분리할 경우, group 도 같이 `sudo chown root:nfc /etc/nfc-agent.env`.

변수 의미는 [[../spec/nfc-agent#환경-변수]]. 시크릿 보관 원칙은 [[security#시크릿-보관-원칙]].

---

## 7. Foreground 검증 (systemd 등록 전 필수)

systemd 등록 전에 직접 실행해서 USB 인식 + 백엔드 도달 + 인증 통과 다 확인. **`sudo` 필수** — Ubuntu polkit 기본 정책상 ssh 세션 user 는 pcscd 못 씀 (systemd 등록 후엔 root 로 돌아서 자연 해결):

```bash
sudo bash -c '
  set -a; source /etc/nfc-agent.env; set +a
  cd /opt/summer_star_company/agent
  /home/'"$USER"'/.local/bin/uv run python -m nfc_agent
'
```

카드 태그 → 백엔드 `access_logs` 에 row 들어가면 성공. Ctrl+C 로 종료.

---

## 8. systemd 등록

위 검증 통과 후:

```bash
sudo cp /opt/summer_star_company/agent/systemd/nfc-agent.service /etc/systemd/system/
# WorkingDirectory 경로 보정 — repo 클론 경로로 맞춤
sudo sed -i 's|/opt/nfc-agent|/opt/summer_star_company/agent|g' /etc/systemd/system/nfc-agent.service
# User 보정 — 1인 운영, polkit 우회 단순화 (보안 강화는 후순위)
sudo sed -i 's|^User=nfc|User=root|' /etc/systemd/system/nfc-agent.service
sudo systemctl daemon-reload
sudo systemctl enable --now nfc-agent
sudo systemctl status nfc-agent --no-pager -l
journalctl -u nfc-agent -f
```

서비스 단위 정의 SSOT 는 [[../spec/nfc-agent#systemd-운영]].

> nfc 전용 유저 분리는 [[security#pi-보안]] 권장이지만, polkit 룰 + group 동기화 부담 → 1인 자호스팅이라 일단 root. 후순위 강화 항목.

---

## 운영

### 네트워크 변경 (이사 / WiFi 전환)

WiFi 환경 바뀌면 (예: 사무실 → 집) 새 SSID 등록:

```bash
sudo nmtui    # 텍스트 GUI: Activate a connection → SSID 선택 → 비번 입력 → Back → Quit
```

또는 한 줄:
```bash
sudo nmcli device wifi connect "<SSID>" password "<비번>"
```

NetworkManager 가 `/etc/NetworkManager/system-connections/<SSID>.nmconnection` 으로 저장 + autoconnect=yes 기본 → 재부팅 시 자동 연결.

연결 확인:
```bash
ip a | grep inet
ping -c 3 8.8.8.8
```

### Agent 상태 / 로그

```bash
sudo systemctl status nfc-agent           # active (running) 떠야 OK
sudo journalctl -u nfc-agent -n 50        # 최근 50줄
sudo journalctl -u nfc-agent -f           # 실시간 (Ctrl+C 종료)
```

카드 태그 → 로그 패턴:
- 정상: `UID=... allowed=True` + `✓ 허용`
- 백엔드 도달 실패: `WARNING 백엔드 push 실패: ...` + `✗ 거부`

### Agent 재시작 / .env 갱신 후

```bash
sudo systemctl restart nfc-agent
sudo journalctl -u nfc-agent -n 20 --no-pager
```

---

## 트러블슈팅

| 증상 | 원인 / 해결 |
|---|---|
| `pcsc_scan` 에서 리더 안 보임 | 2단계 모듈 블랙리스트 누락. `lsmod \| grep -E 'nfc\|pn533'` 비어있어야 함 |
| `pcsc_scan` 안에서 `LIBUSB_ERROR_TIMEOUT` + `Failed adding USB device` 반복 | 전력 부족 가능성 — USB 포트 변경 (Zero3 헤더 USB ↔ 본체 USB) 또는 셀프-파워 허브 |
| `pcsc_scan` 시 `SCardEstablishContext: Access denied` | pcscd 데몬 비활성/권한. `sudo systemctl enable --now pcscd` + `sudo pcsc_scan` 로 분리 진단 |
| Python `EstablishContextException Access denied (0x8010006A)` | Ubuntu polkit 정책상 ssh user 가 pcscd 거부. foreground 검증은 `sudo` 로 실행 (7단계). systemd 등록 후엔 root 라 자연 해결 |
| ACR122U USB 인식 자체 안 됨 (`lsusb` 에 없음) | 1단계 `libccid` + `libacsccid1` 누락 또는 USB 포트 문제 |
| 카드 태그 시 USB disconnect/reset 반복 (`dmesg -w`) | 전력 부족 — 5V/3A 정격 어댑터 또는 셀프-파워 USB 허브 |
| `uv sync` swig/pcsclite 에러 | 1단계 패키지 누락. `swig`, `libpcsclite-dev`, `python3-dev` 재설치 |
| 백엔드 401 | `AGENT_API_KEY` 가 홈서버 값과 다름 |
| 백엔드 도달 실패 (timeout) | 도메인 인증서 미완성 / 공유기 포트포워딩 / 방화벽. 임시 LAN IP 로 분리 검증 |
| systemd 가 시작 안 함 | `journalctl -u nfc-agent -n 50` — 보통 `WorkingDirectory` 경로 또는 `EnvironmentFile` 권한 문제 |

---

## 참고

- [[../spec/nfc-agent]] — 에이전트 동작 / systemd 단위 SSOT
- [[security#pi-보안]] — Pi 보안 가이드
- [[overview]]
