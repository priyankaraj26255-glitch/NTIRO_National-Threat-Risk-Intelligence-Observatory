from datetime import datetime
from sqlalchemy import CheckConstraint

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
    CheckConstraint(
        "approval_status IN ('pending', 'approved', 'rejected', 'not_required')",
        name="ck_users_approval_status",
    ),
    CheckConstraint(
        "account_status IN ('active', 'suspended', 'disabled')",
        name="ck_users_account_status",
    ),
)

    id: Mapped[int] = mapped_column(primary_key=True)

    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
    )

    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=text("false"),
        nullable=False,
    )

    approval_status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        server_default=text("'pending'"),
        nullable=False,
    )

    account_status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        server_default=text("'active'"),
        nullable=False,
    )

    approved_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )