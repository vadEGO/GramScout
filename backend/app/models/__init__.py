import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), index=True)
    tone: Mapped[str] = mapped_column(String(50))
    use_case: Mapped[str] = mapped_column(String(200))
    system_prompt: Mapped[str] = mapped_column(Text)
    user_prompt_template: Mapped[str] = mapped_column(Text)
    examples: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    temperature: Mapped[float] = mapped_column(default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, default=100)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    version: Mapped[int] = mapped_column(Integer, default=1)


class ProtectionPattern(Base):
    __tablename__ = "protection_patterns"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    action_sequence: Mapped[dict] = mapped_column(JSON)
    accounts_used: Mapped[int] = mapped_column(Integer, default=0)
    total_bans: Mapped[int] = mapped_column(Integer, default=0)
    ban_rate: Mapped[float] = mapped_column(default=0.0)
    is_safe: Mapped[bool] = mapped_column(default=True)
    last_tested: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BanEvent(Base):
    __tablename__ = "ban_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    account_id: Mapped[str] = mapped_column(String(36), index=True)
    channel: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    actions_before_ban: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    analyzed: Mapped[bool] = mapped_column(default=False)
