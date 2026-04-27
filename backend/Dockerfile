# 로컬 docker 테스트용. 운영(집 서버) 배포 시 별도 점검 필요.
FROM python:3.13-slim

# pyscard 빌드 + 런타임 (PC/SC 인터페이스)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    swig \
    libpcsclite-dev \
    pcscd \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app

# 의존성 캐시 레이어
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# 앱 코드
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY scripts/ ./scripts/

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
