"""인증 HTTP I/O 스키마. SSOT는 docs/spec/backend-api#auth."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    password: str


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    role: str


class LoginResponse(BaseModel):
    token: str
    user: UserPublic
