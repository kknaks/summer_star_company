"""Access HTTP I/O 스키마. SSOT는 docs/spec/backend-api#access."""

from datetime import datetime

from pydantic import BaseModel, Field


class AccessRequest(BaseModel):
    """Pi 에이전트 push 페이로드."""

    uid: str = Field(min_length=1, max_length=32)
    occurred_at: datetime


class AccessResponse(BaseModel):
    allowed: bool
