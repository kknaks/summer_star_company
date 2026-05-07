"""0005_access_logs_manual_source_and_voided

Revision ID: 832a6d99d1d8
Revises: bbc71b77fe66
Create Date: 2026-05-07 21:19:43.033742

수동 입력 (admin 보정) 지원: source enum, voided/note/created_by_user_id 컬럼 추가.
uid를 nullable 로 변경 (수동 입력은 NULL).
CHECK 제약: 카드 탭은 uid 필수, 수동은 user_id+allowed=true+uid NULL 강제.
인덱스를 WHERE NOT voided 부분 인덱스로 교체 (통계는 voided 제외 기본).

SSOT:
- docs/domain/access-log#수동-입력-admin-crud
- docs/spec/database#access_logs
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "832a6d99d1d8"
down_revision: str | Sequence[str] | None = "bbc71b77fe66"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. enum 생성 + source 컬럼 추가 (default 'card' 로 기존 row 자동 채움)
    op.execute("CREATE TYPE access_log_source AS ENUM ('card', 'manual')")
    op.add_column(
        'access_logs',
        sa.Column(
            'source',
            sa.Enum('card', 'manual', name='access_log_source', create_type=False),
            nullable=False,
            server_default=sa.text("'card'"),
        ),
    )
    # 2. voided / note / created_by_user_id 추가
    op.add_column(
        'access_logs',
        sa.Column('voided', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')),
    )
    op.add_column('access_logs', sa.Column('note', sa.Text(), nullable=True))
    op.add_column(
        'access_logs',
        sa.Column('created_by_user_id', sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        'access_logs_created_by_user_id_fkey',
        'access_logs',
        'users',
        ['created_by_user_id'],
        ['id'],
        ondelete='SET NULL',
    )

    # 3. uid를 nullable 로 (수동 입력은 NULL)
    op.alter_column('access_logs', 'uid', existing_type=sa.Text(), nullable=True)

    # 4. CHECK 제약 — 기존 row 는 source='card' + uid NOT NULL 이라 항상 통과
    op.create_check_constraint(
        'access_logs_source_card_chk',
        'access_logs',
        "source = 'manual' OR uid IS NOT NULL",
    )
    op.create_check_constraint(
        'access_logs_source_manual_chk',
        'access_logs',
        "source = 'card' OR (user_id IS NOT NULL AND uid IS NULL AND allowed = TRUE)",
    )

    # 5. 기존 인덱스를 WHERE NOT voided 부분 인덱스로 교체
    op.drop_index('access_logs_occurred_at_idx', table_name='access_logs')
    op.drop_index('access_logs_user_id_occurred_idx', table_name='access_logs')
    # uid 인덱스는 voided 무관하게 추적용(미등록 카드 등) → 그대로 둠. 다만 uid IS NOT NULL 부분 인덱스로 재생성.
    op.drop_index('access_logs_uid_occurred_idx', table_name='access_logs')

    op.create_index(
        'access_logs_occurred_at_idx',
        'access_logs',
        [sa.literal_column('occurred_at DESC')],
        postgresql_where=sa.text('NOT voided'),
    )
    op.create_index(
        'access_logs_user_id_occurred_idx',
        'access_logs',
        ['user_id', sa.literal_column('occurred_at DESC')],
        postgresql_where=sa.text('NOT voided'),
    )
    op.create_index(
        'access_logs_uid_occurred_idx',
        'access_logs',
        ['uid', sa.literal_column('occurred_at DESC')],
        postgresql_where=sa.text('uid IS NOT NULL'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('access_logs_uid_occurred_idx', table_name='access_logs')
    op.drop_index('access_logs_user_id_occurred_idx', table_name='access_logs')
    op.drop_index('access_logs_occurred_at_idx', table_name='access_logs')

    op.create_index(
        'access_logs_occurred_at_idx',
        'access_logs',
        [sa.literal_column('occurred_at DESC')],
    )
    op.create_index(
        'access_logs_user_id_occurred_idx',
        'access_logs',
        ['user_id', sa.literal_column('occurred_at DESC')],
    )
    op.create_index(
        'access_logs_uid_occurred_idx',
        'access_logs',
        ['uid', sa.literal_column('occurred_at DESC')],
    )

    op.drop_constraint('access_logs_source_manual_chk', 'access_logs', type_='check')
    op.drop_constraint('access_logs_source_card_chk', 'access_logs', type_='check')

    # uid NOT NULL 복구 — 다운그레이드 시점에 manual row가 있으면 실패해야 정상
    op.alter_column('access_logs', 'uid', existing_type=sa.Text(), nullable=False)

    op.drop_constraint('access_logs_created_by_user_id_fkey', 'access_logs', type_='foreignkey')
    op.drop_column('access_logs', 'created_by_user_id')
    op.drop_column('access_logs', 'note')
    op.drop_column('access_logs', 'voided')
    op.drop_column('access_logs', 'source')
    op.execute('DROP TYPE access_log_source')
