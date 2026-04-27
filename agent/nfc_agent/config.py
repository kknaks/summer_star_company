"""에이전트 환경설정. root .env 공유."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# agent/nfc_agent/config.py → repo root
ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    API_BASE_URL: str
    AGENT_API_KEY: str
    READER_NAME: str = "ACR122U"
    HTTP_TIMEOUT_SEC: int = 5
    LOG_LEVEL: str = "INFO"


settings = Settings()
