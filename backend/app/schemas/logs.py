"""Logs HTTP I/O. SSOT는 docs/spec/backend-api#logs."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AccessLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    occurred_at: datetime
    received_at: datetime
    uid: str
    card_id: UUID | None
    user_id: UUID | None
    allowed: bool


class AccessLogListResponse(BaseModel):
    items: list[AccessLogResponse]
    next_cursor: str | None
