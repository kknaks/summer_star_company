"""
SQLAlchemy 모델. 스키마 SSOT는 docs/spec/database.md.
도메인 의미는 docs/domain/{user,card,access-log}.md 참조.
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Text, text
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserRole(StrEnum):
    admin = "admin"


user_role_enum = PgEnum(UserRole, name="user_role", create_type=True)


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        user_role_enum, nullable=False, server_default=text("'admin'")
    )
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    uid: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    user_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    label: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    __table_args__ = (
        Index("cards_user_id_idx", "user_id"),
        Index(
            "cards_active_idx",
            "active",
            postgresql_where=text("active = TRUE"),
        ),
    )


class AccessLog(Base):
    __tablename__ = "access_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    uid: Mapped[str] = mapped_column(Text, nullable=False)
    card_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("cards.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    allowed: Mapped[bool] = mapped_column(Boolean, nullable=False)

    __table_args__ = (
        Index("access_logs_occurred_at_idx", text("occurred_at DESC")),
        Index("access_logs_user_id_occurred_idx", "user_id", text("occurred_at DESC")),
        Index("access_logs_uid_occurred_idx", "uid", text("occurred_at DESC")),
    )
