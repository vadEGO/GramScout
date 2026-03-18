import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


class ActionType(str, enum.Enum):
    SUBSCRIBE = "subscribe"
    COMMENT = "comment"
    REACT = "react"
    READ = "read"
    JOIN = "join"
    LEAVE = "leave"
    VIEW_PROFILE = "view_profile"


class ActionResult(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"
    MUTED = "muted"
    BANNED = "banned"
    TIMEOUT = "timeout"


class ActionLog(Base):
    __tablename__ = "action_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("accounts.id"), index=True
    )
    action_type: Mapped[ActionType] = mapped_column(SQLEnum(ActionType))
    target_channel: Mapped[str | None] = mapped_column(String(500), nullable=True)
    target_post_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    delay_ms: Mapped[int] = mapped_column(Integer, default=0)
    result: Mapped[ActionResult] = mapped_column(SQLEnum(ActionResult))
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    account = relationship("Account", back_populates="action_logs")
