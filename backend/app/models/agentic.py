import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Workflow(Base):
    """Pre-defined multi-step automation workflows for agent use."""

    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="idle"
    )  # idle, running, paused, completed, failed
    steps: Mapped[dict] = mapped_column(
        JSON
    )  # [{step, action, params, status, result}]
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    config: Mapped[dict] = mapped_column(JSON, default=dict)  # workflow-level config
    stats: Mapped[dict] = mapped_column(JSON, default=dict)  # runtime stats
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    triggered_by: Mapped[str] = mapped_column(
        String(50), default="manual"
    )  # manual, agent, cron


class RevenueEvent(Base):
    """Track revenue-generating events."""

    __tablename__ = "revenue_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    event_type: Mapped[str] = mapped_column(
        String(50)
    )  # click, conversion, sale, referral
    source: Mapped[str] = mapped_column(String(100))  # channel, campaign, etc
    affiliate_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    account_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    channel: Mapped[str | None] = mapped_column(String(200), nullable=True)
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AffiliateLink(Base):
    """Track affiliate/referral links."""

    __tablename__ = "affiliate_links"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100))
    url: Mapped[str] = mapped_column(String(500))
    campaign: Mapped[str | None] = mapped_column(String(100), nullable=True)
    channel_target: Mapped[str | None] = mapped_column(String(200), nullable=True)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    revenue: Mapped[float] = mapped_column(Float, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BudgetConfig(Base):
    """Budget and spending limits."""

    __tablename__ = "budget_config"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    category: Mapped[str] = mapped_column(String(50))  # proxies, accounts, ai, total
    daily_limit: Mapped[float] = mapped_column(Float, default=100.0)
    monthly_limit: Mapped[float] = mapped_column(Float, default=1000.0)
    daily_spent: Mapped[float] = mapped_column(Float, default=0.0)
    monthly_spent: Mapped[float] = mapped_column(Float, default=0.0)
    alert_at_pct: Mapped[float] = mapped_column(Float, default=80.0)
    auto_stop_at_limit: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AgentTask(Base):
    """Task queue for autonomous agent operation."""

    __tablename__ = "agent_tasks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    task_type: Mapped[str] = mapped_column(
        String(50)
    )  # import_accounts, warm, comment, parse, boost
    priority: Mapped[int] = mapped_column(Integer, default=5)  # 1=highest, 10=lowest
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, running, completed, failed
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
