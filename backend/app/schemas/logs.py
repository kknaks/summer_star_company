"""Logs HTTP I/O. SSOT는 docs/spec/backend-api#logs."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AccessLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    occurred_at: datetime
    received_at: datetime
    uid: str | None
    card_id: UUID | None
    user_id: UUID | None
    allowed: bool
    source: Literal["card", "manual"]
    created_by_user_id: UUID | None
    voided: bool
    note: str | None


class AccessLogListResponse(BaseModel):
    items: list[AccessLogResponse]
    next_cursor: str | None


class AccessLogCreateRequest(BaseModel):
    user_id: UUID
    occurred_at: datetime
    note: str | None = None


class AccessLogUpdateRequest(BaseModel):
    """수정 요청. 모든 필드 optional. 빠진 필드는 변경 X.

    note 는 명시적으로 null 보내면 비움 — Pydantic 의 model_fields_set 으로 구분.
    """
    model_config = ConfigDict(extra="forbid")

    occurred_at: datetime | None = None
    note: str | None = None
    voided: bool | None = None
