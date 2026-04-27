"""Card HTTP I/O 스키마. SSOT는 docs/spec/backend-api#cards."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CardCreate(BaseModel):
    uid: str = Field(min_length=4, max_length=32)  # raw 입력, 서버에서 정규화
    user_id: UUID
    label: str | None = Field(default=None, max_length=50)


class CardUpdate(BaseModel):
    label: str | None = Field(default=None, max_length=50)
    active: bool | None = None


class CardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    uid: str
    user_id: UUID
    label: str | None
    active: bool
    registered_at: datetime
    created_at: datetime
    updated_at: datetime
