import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AccountChannelTarget(Base):
    """Many-to-many: accounts assigned to target specific channels."""

    __tablename__ = "account_channel_targets"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("accounts.id", ondelete="CASCADE"), index=True
    )
    channel_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("channels.id", ondelete="CASCADE"), index=True
    )
    priority: Mapped[int] = mapped_column(Integer, default=5)  # 1=highest
    actions_per_day: Mapped[int] = mapped_column(Integer, default=5)
    comment_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    react_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    subscribe_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
