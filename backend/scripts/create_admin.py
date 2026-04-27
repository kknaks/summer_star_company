"""초기 admin 사용자 생성 CLI.

사용:
    cd backend && uv run python scripts/create_admin.py --name admin --password "..."

이미 admin이 존재하면 중복 생성하지 않음.
"""

import argparse
import asyncio
import sys
from pathlib import Path

# scripts/는 backend/ 패키지 외부라 sys.path에 backend/ 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.base import SessionLocal  # noqa: E402
from app.db.models import User, UserRole  # noqa: E402


async def create_admin(name: str, password: str) -> int:
    async with SessionLocal() as session:
        existing = await session.scalar(
            select(User).where(User.role == UserRole.admin, User.active.is_(True))
        )
        if existing is not None:
            print(f"⚠ 이미 admin 존재: {existing.name} (id={existing.id})")
            return 1

        user = User(
            name=name,
            role=UserRole.admin,
            password_hash=hash_password(password),
            active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        print(f"✓ admin 생성: {user.name} (id={user.id})")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="초기 admin 사용자 생성")
    parser.add_argument("--name", required=True, help="표시명")
    parser.add_argument("--password", required=True, help="비밀번호 (bcrypt 해싱)")
    args = parser.parse_args()
    return asyncio.run(create_admin(args.name, args.password))


if __name__ == "__main__":
    sys.exit(main())
