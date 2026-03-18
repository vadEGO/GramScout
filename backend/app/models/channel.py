import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    url: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    subscribers: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    topic: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_target: Mapped[bool] = mapped_column(Boolean, default=False)
    open_comments: Mapped[bool] = mapped_column(Boolean, default=True)
    spam_rating: Mapped[int] = mapped_column(Integer, default=0)
    quality_score: Mapped[float] = mapped_column(default=0.0)
    last_parsed: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
