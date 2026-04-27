"""FastAPI 진입점. startup 시 Alembic 마이그레이션 자동 적용."""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from alembic.config import Config as AlembicConfig
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from alembic import command
from app.api import access as access_api
from app.api import auth as auth_api
from app.api import cards as cards_api
from app.api import logs as logs_api
from app.api import stats as stats_api
from app.api import users as users_api
from app.core.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

BACKEND_DIR = Path(__file__).resolve().parent.parent  # app/main.py → backend/


def run_migrations() -> None:
    cfg = AlembicConfig(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    logger.info("alembic upgrade head 실행")
    # alembic env.py가 내부적으로 asyncio.run()을 쓰므로 별도 스레드에서 실행
    await asyncio.to_thread(run_migrations)
    logger.info("마이그레이션 완료")
    yield


app = FastAPI(title="Summer Star Company API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=False,
)


app.include_router(auth_api.router)
app.include_router(users_api.router)
app.include_router(cards_api.router)
app.include_router(access_api.router)
app.include_router(logs_api.router)
app.include_router(stats_api.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
