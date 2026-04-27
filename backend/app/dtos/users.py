"""User 관련 내부 DTO. service ↔ router 사이의 전달."""

from dataclasses import dataclass
from datetime import datetime

from app.db.models import User


@dataclass
class UserListItem:
    user: User
    card_count: int
    last_access_at: datetime | None
