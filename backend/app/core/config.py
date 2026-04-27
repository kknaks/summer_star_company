from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py → repo root
ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str
    JWT_SECRET: str = "dev-only-not-for-prod"
    AGENT_API_KEY: str = "dev-only-not-for-prod"
    CORS_ORIGINS: str = "http://localhost:3000"

    READER_NAME: str = "ACR122U"
    READER_TIMEOUT_SEC: int = 30

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
