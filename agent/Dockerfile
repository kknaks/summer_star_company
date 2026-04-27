# 로컬 docker 테스트용. 운영(라즈베리파이) 배포는 systemd 직접 ([[../systemd/nfc-agent.service]]).
#
# ⚠ macOS Docker는 USB 패스스루를 지원 안 함 — 컨테이너 안에서 ACR122U 못 봄.
# Linux/Pi에서 실제 카드 테스트하려면 compose에 `devices: ["/dev/bus/usb:/dev/bus/usb"]` 추가.
FROM python:3.13-slim

# pyscard 빌드 + 런타임
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    swig \
    libpcsclite-dev \
    pcscd \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY nfc_agent/ ./nfc_agent/

ENV PATH="/app/.venv/bin:$PATH"

CMD ["python", "-m", "nfc_agent"]
