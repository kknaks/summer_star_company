"""0003 add staff role

Revision ID: 0229e3701d37
Revises: 6b91d586f035
Create Date: 2026-05-06 23:43:37.237677

ENUM ADD VALUE 만 단독 revision. 이 값을 사용하는 UPDATE 는 0004 에서.
Postgres 12+ 는 ADD VALUE 를 트랜잭션 내에서 허용하지만, 같은 트랜잭션에서 사용은
불가 — env.py 의 transaction_per_migration=True 와 함께 분리 필요.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '0229e3701d37'
down_revision: Union[str, Sequence[str], None] = '6b91d586f035'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'staff'")


def downgrade() -> None:
    """Downgrade schema."""
    # Postgres 는 ENUM 값 제거를 직접 지원하지 않음. 타입 재생성 필요.
    # 1인 운영 스코프상 down 경로 무시 (운영에서 down 안 함).
    pass
