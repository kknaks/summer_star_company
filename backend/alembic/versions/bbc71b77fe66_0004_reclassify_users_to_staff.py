"""0004 reclassify users to staff

Revision ID: bbc71b77fe66
Revises: 0229e3701d37
Create Date: 2026-05-06 23:43:40.981251

password_hash 가 없는 사용자(=직원) 는 staff 로 재분류.
password_hash 있는 사용자만 admin 로 유지 (1인 admin 가정).
컬럼 default 도 'staff' 로 변경 — 신규 유저는 자동 staff.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bbc71b77fe66'
down_revision: Union[str, Sequence[str], None] = '0229e3701d37'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "UPDATE users SET role = 'staff' WHERE password_hash IS NULL"
    )
    op.alter_column(
        'users',
        'role',
        server_default=sa.text("'staff'"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'users',
        'role',
        server_default=sa.text("'admin'"),
    )
    op.execute("UPDATE users SET role = 'admin'")
