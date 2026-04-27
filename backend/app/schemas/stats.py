"""Stats HTTP I/O. SSOT는 docs/spec/backend-api#stats."""

from pydantic import BaseModel


class DailyStatResponse(BaseModel):
    date: str  # "YYYY-MM-DD"
    first_in: str  # "HH:MM" KST
    last_out: str
    duration_minutes: int


class MonthlyStatResponse(BaseModel):
    month: str  # "YYYY-MM"
    work_days: int
    avg_first_in: str
    avg_last_out: str
    avg_duration_minutes: int
