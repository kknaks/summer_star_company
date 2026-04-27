"""Access 관련 내부 DTO + cursor 페이지네이션 인코딩."""

import base64
import json
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CursorParts:
    occurred_at: datetime
    log_id: int


def encode_cursor(occurred_at: datetime, log_id: int) -> str:
    payload = json.dumps([occurred_at.isoformat(), log_id])
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("utf-8")


def decode_cursor(token: str) -> CursorParts:
    payload = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
    dt_str, log_id = json.loads(payload)
    return CursorParts(occurred_at=datetime.fromisoformat(dt_str), log_id=int(log_id))
