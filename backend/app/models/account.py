import uuid
from datetime import datetime
from sqlalchemy import (
    String,
    Boolean,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


class AccountStatus(str, enum.Enum):
    ACTIVE = "active"
    WARMING = "warming"
    WORKING = "working"
    MUTED = "muted"
    BANNED = "banned"
    INVALID = "invalid"


class AccountFormat(str, enum.Enum):
    TDATA = "tdata"
    SESSION = "session"
    MANUAL = "manual"


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    country_code: Mapped[str] = mapped_column(String(5))
    geo: Mapped[str] = mapped_column(String(10))
    format: Mapped[AccountFormat] = mapped_column(SQLEnum(AccountFormat))
    proxy_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("proxies.id"), nullable=True
    )
    status: Mapped[AccountStatus] = mapped_column(
        SQLEnum(AccountStatus), default=AccountStatus.ACTIVE
    )
    premium: Mapped[bool] = mapped_column(Boolean, default=False)
    premium_expiry: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    registration_age_days: Mapped[int] = mapped_column(Integer, default=0)
    gender: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # male, female, unspecified
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(200), nullable=True)
    session_string: Mapped[str | None] = mapped_column(String, nullable=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dc_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ban_count: Mapped[int] = mapped_column(Integer, default=0)
    warming_stage: Mapped[int] = mapped_column(Integer, default=0)
    assigned_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    persona: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    proxy = relationship("Proxy", back_populates="accounts")
    action_logs = relationship("ActionLog", back_populates="account")
