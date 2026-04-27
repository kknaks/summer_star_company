"""출퇴근 통계 라우터. KST 04:00 컷오프."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, SessionDep
from app.schemas.stats import DailyStatResponse, MonthlyStatResponse
from app.services import stats_service

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/daily", response_model=list[DailyStatResponse])
async def daily_stats(
    session: SessionDep,
    _: CurrentUser,
    user_id: UUID,
    year: Annotated[int, Query(ge=2020, le=2100)],
    month: Annotated[int, Query(ge=1, le=12)],
) -> list[DailyStatResponse]:
    items = await stats_service.daily_stats_for_month(session, user_id, year, month)
    return [DailyStatResponse(**vars(it)) for it in items]


@router.get("/monthly", response_model=list[MonthlyStatResponse])
async def monthly_stats(
    session: SessionDep,
    _: CurrentUser,
    user_id: UUID,
    year: Annotated[int, Query(ge=2020, le=2100)],
) -> list[MonthlyStatResponse]:
    items = await stats_service.monthly_stats_for_year(session, user_id, year)
    return [MonthlyStatResponse(**vars(it)) for it in items]
