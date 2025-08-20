from datetime import datetime

from sqlalchemy import ForeignKey, String, BigInteger, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class File(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    content_type: Mapped[str] = mapped_column(String, nullable=False)
    size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    storage_key: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    owner: Mapped["User"] = relationship("User", back_populates="files")