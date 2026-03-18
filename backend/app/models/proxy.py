import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Proxy(Base):
    __tablename__ = "proxies"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    ip: Mapped[str] = mapped_column(String(45))
    port: Mapped[int] = mapped_column(Integer)
    username: Mapped[str] = mapped_column(String(100))
    password: Mapped[str] = mapped_column(String(100))
    protocol: Mapped[str] = mapped_column(String(10), default="SOCKS5")
    country: Mapped[str] = mapped_column(String(10))
    provider: Mapped[str] = mapped_column(String(100))
    purchase_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expiry_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ban_rate: Mapped[float] = mapped_column(Float, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_check: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    accounts = relationship("Account", back_populates="proxy")
