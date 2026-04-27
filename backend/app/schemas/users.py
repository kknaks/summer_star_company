"""User HTTP I/O 스키마. SSOT는 docs/spec/backend-api#users."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    active: bool | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    role: str
    active: bool
    created_at: datetime
    updated_at: datetime


class UserListItemResponse(UserResponse):
    """목록 응답: 기본 + 집계 필드."""

    card_count: int = 0
    last_access_at: datetime | None = None
