
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SourceReport(Base):
    __tablename__ = "source_reports"

    __table_args__ = (
        CheckConstraint(
            "review_status IN "
            "('pending_review', 'under_review', 'reviewed', "
            "'rejected', 'needs_more_information')",
            name="ck_source_report_review_status",
        ),
        CheckConstraint(
            "evidence_status IN "
            "('unassessed', 'unverified', 'corroborated', "
            "'officially_confirmed', 'disputed')",
            name="ck_source_report_evidence_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    incident_id: Mapped[int | None] = mapped_column(
        ForeignKey("incidents.id"),
        nullable=True,
    )

    source_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    source_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    source_location_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    incident_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    reported_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    review_status: Mapped[str] = mapped_column(
        String(30),
        default="pending_review",
        server_default=text("'pending_review'"),
        nullable=False,
    )

    evidence_status: Mapped[str] = mapped_column(
        String(30),
        default="unassessed",
        server_default=text("'unassessed'"),
        nullable=False,
    )
