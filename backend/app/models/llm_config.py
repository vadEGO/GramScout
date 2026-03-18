import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LLMProvider(Base):
    """LLM provider configuration (OpenRouter, OpenAI, Anthropic, etc)."""

    __tablename__ = "llm_providers"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100))
    provider_type: Mapped[str] = mapped_column(
        String(50)
    )  # openrouter, openai, anthropic, google, local
    api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=5)  # lower = preferred
    daily_limit_usd: Mapped[float] = mapped_column(Float, default=10.0)
    daily_spend_usd: Mapped[float] = mapped_column(Float, default=0.0)
    total_spend_usd: Mapped[float] = mapped_column(Float, default=0.0)
    rate_limit_rpm: Mapped[int] = mapped_column(Integer, default=60)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class LLMModelConfig(Base):
    """Per-model configuration and preferences."""

    __tablename__ = "llm_model_configs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    provider_id: Mapped[str] = mapped_column(String(36), nullable=True)
    model_id: Mapped[str] = mapped_column(String(200))  # e.g., "openai/gpt-4o-mini"
    display_name: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(
        String(50), default="general"
    )  # general, commenting, dialogue, analysis, troubleshoot
    cost_per_1m_input: Mapped[float] = mapped_column(Float, default=0.0)
    cost_per_1m_output: Mapped[float] = mapped_column(Float, default=0.0)
    max_tokens: Mapped[int] = mapped_column(Integer, default=4096)
    supports_functions: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    quality_score: Mapped[float] = mapped_column(Float, default=5.0)  # 1-10
    speed_score: Mapped[float] = mapped_column(Float, default=5.0)  # 1-10
    total_requests: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens_input: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens_output: Mapped[int] = mapped_column(Integer, default=0)
    total_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TroubleshootSession(Base):
    """LLM troubleshooting sessions."""

    __tablename__ = "troubleshoot_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_query: Mapped[str] = mapped_column(Text)
    diagnosis: Mapped[str | None] = mapped_column(Text, nullable=True)
    fixes_applied: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    logs_analyzed: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, analyzing, fix_available, applied, failed
    model_used: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
