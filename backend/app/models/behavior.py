import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BehaviorProfile(Base):
    """Behavior profiles that control how accounts act."""

    __tablename__ = "behavior_profiles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100))
    profile_type: Mapped[str] = mapped_column(
        String(20)
    )  # conservative, moderate, aggressive

    # Activity rates
    comments_per_day_max: Mapped[int] = mapped_column(Integer, default=5)
    reactions_per_day_max: Mapped[int] = mapped_column(Integer, default=20)
    reads_per_day_max: Mapped[int] = mapped_column(Integer, default=100)
    joins_per_day_max: Mapped[int] = mapped_column(Integer, default=3)
    dms_per_day_max: Mapped[int] = mapped_column(Integer, default=10)
    story_views_per_day_max: Mapped[int] = mapped_column(Integer, default=30)

    # Delays (seconds)
    comment_delay_min: Mapped[int] = mapped_column(Integer, default=30)
    comment_delay_max: Mapped[int] = mapped_column(Integer, default=300)
    reaction_delay_min: Mapped[int] = mapped_column(Integer, default=10)
    reaction_delay_max: Mapped[int] = mapped_column(Integer, default=60)
    dm_delay_min: Mapped[int] = mapped_column(Integer, default=60)
    dm_delay_max: Mapped[int] = mapped_column(Integer, default=600)
    join_delay_min: Mapped[int] = mapped_column(Integer, default=120)
    join_delay_max: Mapped[int] = mapped_column(Integer, default=600)

    # Typing simulation
    typing_speed_wpm: Mapped[int] = mapped_column(Integer, default=40)
    typing_speed_variation: Mapped[float] = mapped_column(Float, default=0.3)
    typing_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Reading behavior
    read_before_comment_pct: Mapped[float] = mapped_column(Float, default=0.8)
    scroll_before_action_pct: Mapped[float] = mapped_column(Float, default=0.6)
    view_profile_before_comment_pct: Mapped[float] = mapped_column(Float, default=0.3)

    # Activity patterns
    active_hours_start: Mapped[int] = mapped_column(Integer, default=8)
    active_hours_end: Mapped[int] = mapped_column(Integer, default=23)
    weekend_activity_multiplier: Mapped[float] = mapped_column(Float, default=0.7)
    idle_probability: Mapped[float] = mapped_column(Float, default=0.15)
    idle_duration_min: Mapped[int] = mapped_column(Integer, default=60)
    idle_duration_max: Mapped[int] = mapped_column(Integer, default=300)

    # Anti-detection
    action_randomization: Mapped[bool] = mapped_column(Boolean, default=True)
    interleave_reading: Mapped[bool] = mapped_column(Boolean, default=True)
    random_pause_probability: Mapped[float] = mapped_column(Float, default=0.1)
    max_actions_per_session: Mapped[int] = mapped_column(Integer, default=50)
    session_duration_max_min: Mapped[int] = mapped_column(Integer, default=120)

    # Channel behavior
    join_before_comment: Mapped[bool] = mapped_column(Boolean, default=True)
    join_delay_before_comment_min: Mapped[int] = mapped_column(Integer, default=300)
    join_delay_before_comment_max: Mapped[int] = mapped_column(Integer, default=1800)
    comment_only_after_reads: Mapped[int] = mapped_column(Integer, default=3)

    # Warming intensity (0-100 scale)
    warming_intensity_base: Mapped[int] = mapped_column(Integer, default=50)
    warming_intensity_daily_increase: Mapped[int] = mapped_column(Integer, default=2)

    # Trust decay
    trust_gain_per_clean_day: Mapped[int] = mapped_column(Integer, default=1)
    trust_loss_per_mute: Mapped[int] = mapped_column(Integer, default=3)
    trust_loss_per_ban: Mapped[int] = mapped_column(Integer, default=10)
    trust_loss_per_spamblock: Mapped[int] = mapped_column(Integer, default=15)

    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AccountTrustScore(Base):
    """Per-account trust/health score tracking."""

    __tablename__ = "account_trust_scores"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    account_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    score: Mapped[int] = mapped_column(Integer, default=50)  # 0-100
    health_status: Mapped[str] = mapped_column(
        String(20), default="healthy"
    )  # healthy, warning, critical, quarantine
    last_mute: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_ban: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_spamblock: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total_mutes: Mapped[int] = mapped_column(Integer, default=0)
    total_bans: Mapped[int] = mapped_column(Integer, default=0)
    total_clean_days: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ChannelBlacklist(Base):
    """Channels where accounts got banned/muted."""

    __tablename__ = "channel_blacklist"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    channel_url: Mapped[str] = mapped_column(String(500), index=True)
    channel_username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reason: Mapped[str] = mapped_column(String(50))  # ban, mute, spamblock, manual
    account_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ChannelWhitelist(Base):
    """Channels where accounts successfully operated."""

    __tablename__ = "channel_whitelist"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    channel_url: Mapped[str] = mapped_column(String(500), index=True)
    channel_username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    success_count: Mapped[int] = mapped_column(Integer, default=1)
    last_success: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AccountTag(Base):
    """Tags/roles for organizing accounts."""

    __tablename__ = "account_tags"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100))
    color: Mapped[str] = mapped_column(String(7), default="#3b82f6")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AccountTagAssignment(Base):
    """Many-to-many: accounts to tags."""

    __tablename__ = "account_tag_assignments"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("accounts.id"), index=True
    )
    tag_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("account_tags.id"), index=True
    )


class NeuroDialogueConfig(Base):
    """Neurodialogue configuration for DM auto-reply."""

    __tablename__ = "neuro_dialogue_configs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100))
    system_prompt: Mapped[str] = mapped_column(Text)
    context_message_count: Mapped[int] = mapped_column(Integer, default=10)
    reply_delay_min: Mapped[int] = mapped_column(Integer, default=5)
    reply_delay_max: Mapped[int] = mapped_column(Integer, default=60)
    max_reply_length: Mapped[int] = mapped_column(Integer, default=200)
    language: Mapped[str] = mapped_column(String(10), default="auto")
    product_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    product_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    product_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    organic_promotion_pct: Mapped[int] = mapped_column(Integer, default=15)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class NeuroChatConfig(Base):
    """Neurochat configuration for group/channel monitoring."""

    __tablename__ = "neuro_chat_configs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100))
    mode: Mapped[str] = mapped_column(String(20))  # trigger, interval
    trigger_keywords: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )  # ["keyword1", "keyword2"]
    semantic_matching: Mapped[bool] = mapped_column(Boolean, default=True)
    reply_interval_pct: Mapped[int] = mapped_column(
        Integer, default=50
    )  # % of messages to reply to
    system_prompt: Mapped[str] = mapped_column(Text)
    target_group_urls: Mapped[dict] = mapped_column(JSON)  # ["https://t.me/group1"]
    language: Mapped[str] = mapped_column(String(10), default="auto")
    auto_responder_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_responder_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    context_window: Mapped[int] = mapped_column(Integer, default=15)
    ai_protection_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    protection_mode: Mapped[str] = mapped_column(String(20), default="balanced")
    session_duration_min: Mapped[int] = mapped_column(Integer, default=480)
    max_messages_per_session: Mapped[int] = mapped_column(Integer, default=500)
    messages_before_account_switch: Mapped[int] = mapped_column(Integer, default=10)
    delay_min: Mapped[int] = mapped_column(Integer, default=5)
    delay_max: Mapped[int] = mapped_column(Integer, default=60)
    organic_promotion_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    organic_promotion_pct: Mapped[int] = mapped_column(Integer, default=15)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WarmingPreset(Base):
    """Saved warming configuration presets."""

    __tablename__ = "warming_presets"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100))
    intensity: Mapped[str] = mapped_column(
        String(20)
    )  # conservative, normal, aggressive
    session_duration_min: Mapped[int] = mapped_column(Integer, default=30)
    actions: Mapped[dict] = mapped_column(
        JSON
    )  # {"reactions": true, "reading": true, ...}
    channel_urls: Mapped[dict] = mapped_column(JSON)  # list of channels for warming
    safety_limits: Mapped[dict] = mapped_column(JSON)  # actions/hour, actions/day, etc
    schedule_start: Mapped[int] = mapped_column(Integer, default=0)  # hour
    schedule_end: Mapped[int] = mapped_column(Integer, default=24)  # hour
    stage_adaptation: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
