from sqlalchemy import Boolean, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
class Role(Base):
    __tablename__="roles"
    id:Mapped[int]= mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("true"),
        nullable=False,
    )
