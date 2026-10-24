from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
class State(Base):
    __tablename__ = "states"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )
    code:Mapped[str | None] = mapped_column(
        String(10),
        unique=True,
        nullable=True, 

    )
class District(Base):
    __tablename__ = "districts"

    __table_args__ = (
        UniqueConstraint("state_id", "name", name="uq_district_state_name"),
        UniqueConstraint("id", "state_id", name="uq_district_id_state"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    state_id: Mapped[int] = mapped_column(
        ForeignKey("states.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
