
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.category import IncidentCategory
from app.models.geography import District, State


class Incident(Base):
    __tablename__ = "incidents"

    __table_args__ = (
        ForeignKeyConstraint(
            ["district_id", "state_id"],
            ["districts.id", "districts.state_id"],
            name="fk_incident_district_state",
        ),
        CheckConstraint(
            "district_id IS NULL OR state_id IS NOT NULL",
            name="ck_incident_district_requires_state",
        ),
        CheckConstraint(
            "validation_status IN "
            "('pending_review', 'under_review', 'validated', "
            "'rejected', 'needs_more_information')",
            name="ck_incident_validation_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    category_id: Mapped[int] = mapped_column(
        ForeignKey("incident_categories.id"),
        nullable=False,
    )

    incident_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    state_id: Mapped[int | None] = mapped_column(
        ForeignKey("states.id"),
        nullable=True,
    )

    district_id: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    validation_status: Mapped[str] = mapped_column(
        String(30),
        default="pending_review",
        server_default=text("'pending_review'"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
