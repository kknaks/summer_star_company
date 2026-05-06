"""0002 add user character_id

Revision ID: 6b91d586f035
Revises: 6853668a5e90
Create Date: 2026-05-06 23:03:48.687782

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b91d586f035'
down_revision: Union[str, Sequence[str], None] = '6853668a5e90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'users',
        sa.Column(
            'character_id',
            sa.String(length=16),
            nullable=True,
            server_default='c_f1',
        ),
    )
    op.execute("UPDATE users SET character_id = 'c_f1' WHERE character_id IS NULL")
    op.alter_column('users', 'character_id', nullable=False)
    op.create_check_constraint(
        'users_character_id_chk',
        'users',
        "character_id IN ('c_f1','c_f2','c_m1','c_m2')",
    )
    op.create_index('idx_users_character_id', 'users', ['character_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_users_character_id', table_name='users')
    op.drop_constraint('users_character_id_chk', 'users', type_='check')
    op.drop_column('users', 'character_id')
