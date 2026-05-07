"""Phase 12-B 검증 — 수동 CRUD + admin guard.

서비스 레이어 직접 호출 (insert_manual / update_log / void_log) +
HTTP 레이어 admin guard (httpx).

서비스가 자체 commit 하므로 트랜잭션 롤백 패턴을 못 씀 → 테스트 fixture 는
sentinel uid / note 로 표시해 시작/끝에 DELETE 로 청소.

규칙 SSOT:
- docs/domain/access-log#수동-입력-admin-crud
- docs/spec/backend-api#logs
"""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy import text

from app.core.exceptions import (
    AccessLogImmutableFieldError,
    AccessLogNotFoundError,
    FutureOccurredAtError,
)
from app.core.security import create_access_token
from app.db.base import SessionLocal
from app.db.models import AccessLogSource, UserRole
from app.repos import access_log_repo
from app.services import log_service

KST = ZoneInfo("Asia/Seoul")
ADMIN_ID = UUID("49c45d6e-7f90-425b-83af-c8f2ab92d6c8")
STAFF_ID = UUID("9d220ffb-d623-48e9-8b40-074112c41645")
API = "http://localhost:48000"
SENTINEL_NOTE = "__verify_logs_crud_fixture__"
SENTINEL_UID = "VERIFYTST"


def kst_to_utc(y: int, m: int, d: int, h: int, mi: int = 0) -> datetime:
    return datetime(y, m, d, h, mi, tzinfo=KST).astimezone(UTC)


async def cleanup() -> None:
    async with SessionLocal() as session:
        await session.execute(
            text(
                "DELETE FROM access_logs "
                "WHERE note = :n OR uid = :u"
            ),
            {"n": SENTINEL_NOTE, "u": SENTINEL_UID},
        )
        await session.commit()


async def main() -> int:
    await cleanup()
    results: list[tuple[bool, str]] = []

    # ───── 서비스 레이어 ─────
    async with SessionLocal() as session:
        # 1. 수동 insert 성공 (note=SENTINEL 로 남겨 청소 가능)
        log = await log_service.insert_manual(
            session,
            user_id=STAFF_ID,
            occurred_at=kst_to_utc(2026, 5, 1, 9, 0),
            note=SENTINEL_NOTE,
            actor_id=ADMIN_ID,
        )
        ok = (
            log.source == AccessLogSource.manual
            and log.uid is None
            and log.card_id is None
            and log.allowed is True
            and log.user_id == STAFF_ID
            and log.created_by_user_id == ADMIN_ID
            and log.note == SENTINEL_NOTE
        )
        results.append((ok, "insert_manual 자동 채움 (source/uid/allowed/created_by)"))
        manual_id = log.id

        # 2. 미래 시각 거부
        try:
            await log_service.insert_manual(
                session,
                user_id=STAFF_ID,
                occurred_at=datetime.now(UTC) + timedelta(hours=1),
                note=SENTINEL_NOTE,
                actor_id=ADMIN_ID,
            )
            results.append((False, "future occurred_at 거부 (예외 발생 안 함)"))
        except FutureOccurredAtError:
            results.append((True, "future occurred_at 거부 (FutureOccurredAtError)"))

    # 3. card row insert (sentinel uid)
    async with SessionLocal() as session:
        await session.execute(
            text("""
                INSERT INTO access_logs (occurred_at, user_id, allowed, voided, source, uid)
                VALUES (:o, :u, TRUE, FALSE, 'card', :uid)
            """),
            {"o": kst_to_utc(2026, 5, 1, 18, 0), "u": STAFF_ID, "uid": SENTINEL_UID},
        )
        await session.commit()
        res = await session.execute(
            text("SELECT id FROM access_logs WHERE uid = :u ORDER BY id DESC LIMIT 1"),
            {"u": SENTINEL_UID},
        )
        card_id = res.scalar_one()

    # 4. card row 의 occurred_at 수정 시도 → 422 예외
    async with SessionLocal() as session:
        try:
            await log_service.update_log(
                session,
                log_id=card_id,
                occurred_at=kst_to_utc(2026, 5, 1, 19, 0),
                note_provided=False,
                note=None,
                voided=None,
            )
            results.append((False, "card row occurred_at 수정 거부 (예외 발생 안 함)"))
        except AccessLogImmutableFieldError:
            results.append(
                (True, "card row occurred_at 수정 거부 (AccessLogImmutableFieldError)")
            )

    # 5. card row 의 voided / note 수정은 OK
    async with SessionLocal() as session:
        updated = await log_service.update_log(
            session,
            log_id=card_id,
            occurred_at=None,
            note_provided=True,
            note=SENTINEL_NOTE,
            voided=True,
        )
        results.append(
            (
                updated.voided is True and updated.note == SENTINEL_NOTE,
                "card row voided/note 수정 OK",
            )
        )

    # 6. void → 복구 토글
    async with SessionLocal() as session:
        voided = await log_service.void_log(session, log_id=manual_id)
    async with SessionLocal() as session:
        restored = await log_service.update_log(
            session,
            log_id=manual_id,
            occurred_at=None,
            note_provided=False,
            note=None,
            voided=False,
        )
    results.append(
        (
            voided.voided is True and restored.voided is False,
            "void → 복구 토글",
        )
    )

    # 7. 통계 voided 제외 — 5/1 day 의 두 row 중 card 는 voided=true → manual only
    async with SessionLocal() as session:
        start = kst_to_utc(2026, 5, 1, 4, 0)
        end = kst_to_utc(2026, 6, 1, 4, 0)
        rows = await access_log_repo.daily_stats(
            session, user_id=STAFF_ID, start_utc=start, end_utc=end
        )
        day_5_1 = [r for r in rows if str(r[0]) == "2026-05-01"]
        ok = (
            len(day_5_1) == 1
            and day_5_1[0][1].astimezone(KST).strftime("%H:%M") == "09:00"
            and day_5_1[0][2].astimezone(KST).strftime("%H:%M") == "09:00"
        )
        results.append(
            (ok, "통계 voided 제외 — voided=true card row 제외 후 manual only")
        )

    # 8. 존재 안 하는 log_id → 404 예외
    async with SessionLocal() as session:
        try:
            await log_service.update_log(
                session,
                log_id=999999999,
                occurred_at=None,
                note_provided=False,
                note=None,
                voided=True,
            )
            results.append((False, "404 (존재 안함) - 예외 발생 안 함"))
        except AccessLogNotFoundError:
            results.append((True, "404 (존재 안함) - AccessLogNotFoundError"))

    # ───── HTTP 레이어 admin guard ─────
    admin_token = create_access_token(ADMIN_ID, UserRole.admin.value)
    staff_token = create_access_token(STAFF_ID, UserRole.staff.value)

    async with httpx.AsyncClient() as client:
        # 9. staff token 으로 POST → 403
        r = await client.post(
            f"{API}/api/logs",
            headers={"Authorization": f"Bearer {staff_token}"},
            json={
                "user_id": str(STAFF_ID),
                "occurred_at": "2026-05-01T09:00:00+09:00",
                "note": SENTINEL_NOTE,
            },
        )
        results.append((r.status_code == 403, f"staff POST /api/logs → 403 (got {r.status_code})"))

        # 10. admin token 으로 POST → 201
        r = await client.post(
            f"{API}/api/logs",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "user_id": str(STAFF_ID),
                "occurred_at": "2026-05-01T10:00:00+09:00",
                "note": SENTINEL_NOTE,
            },
        )
        if r.status_code != 201:
            results.append((False, f"admin POST /api/logs → 201 (got {r.status_code}): {r.text}"))
        else:
            log_id = r.json()["id"]
            results.append((True, "admin POST /api/logs → 201"))

            # 11. DELETE → voided
            r = await client.delete(
                f"{API}/api/logs/{log_id}",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            ok = r.status_code == 200 and r.json()["voided"] is True
            results.append(
                (ok, f"admin DELETE /api/logs/{log_id} → 200 voided=true (got {r.status_code})")
            )

            # 12. include_voided=true 면 voided row 포함
            r = await client.get(
                f"{API}/api/logs",
                headers={"Authorization": f"Bearer {admin_token}"},
                params={"user_id": str(STAFF_ID), "include_voided": True, "limit": 50},
            )
            ids = [it["id"] for it in r.json()["items"]]
            results.append(
                (log_id in ids, "GET /api/logs?include_voided=true 에 voided row 포함")
            )

            # 13. include_voided=false (기본) 면 제외
            r = await client.get(
                f"{API}/api/logs",
                headers={"Authorization": f"Bearer {admin_token}"},
                params={"user_id": str(STAFF_ID), "limit": 50},
            )
            ids = [it["id"] for it in r.json()["items"]]
            results.append(
                (log_id not in ids, "GET /api/logs (default) 에 voided row 제외")
            )

    # cleanup
    await cleanup()

    print()
    for ok, name in results:
        print(f"{'✓' if ok else '✗'} {name}")
    passed = sum(1 for ok, _ in results if ok)
    print(f"\n통과: {passed}/{len(results)}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
