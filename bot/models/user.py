from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.models.base import Base


class User(Base):
    __tablename__ = "users"

    # Telegram's own user id is globally unique and stable — reusing it as
    # the primary key avoids a pointless surrogate id and a lookup join on
    # every incoming update.
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tasks: Mapped[list["Task"]] = relationship(back_populates="user", cascade="all, delete-orphan")
