from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import relationship

from app.database import Base

from datetime import datetime, timezone

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="user", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    refresh_tokens = relationship("RefreshToken", cascade="all, delete-orphan", back_populates="user")
    files: Mapped[list["File"]] = relationship(back_populates="owner", cascade="all, delete-orphan")

