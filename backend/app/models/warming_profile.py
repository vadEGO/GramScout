import uuid
import json
from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WarmingProfile(Base):
    """Fine-grained warming profile with per-stage configuration."""

    __tablename__ = "warming_profiles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Initial rest period after import (hours)
    initial_rest_hours_min: Mapped[int] = mapped_column(Integer, default=12)
    initial_rest_hours_max: Mapped[int] = mapped_column(Integer, default=24)

    # Per-account-action weights (JSON: {"read": 7, "react": 3, "subscribe": 1, ...})
    action_weights: Mapped[dict] = mapped_column(
        JSON,
        default=lambda: {
            "read": 7,
            "react": 3,
            "view_profile": 2,
            "subscribe": 1,
            "comment": 0,
        },
    )

    # Stage thresholds (JSON array of stage configs)
    stages: Mapped[dict] = mapped_column(
        JSON,
        default=lambda: [
            {
                "name": "Cold Start",
                "stage_min": 0,
                "stage_max": 10,
                "actions_per_hour": 3,
                "session_duration_min": 15,
                "rest_between_sessions_hours": 12,
                "max_sessions_per_day": 2,
                "allowed_actions": ["read", "view_profile"],
                "action_weights_override": {"read": 8, "view_profile": 2},
            },
            {
                "name": "Early Warming",
                "stage_min": 10,
                "stage_max": 30,
                "actions_per_hour": 5,
                "session_duration_min": 25,
                "rest_between_sessions_hours": 8,
                "max_sessions_per_day": 2,
                "allowed_actions": ["read", "react", "view_profile"],
                "action_weights_override": {"read": 5, "react": 3, "view_profile": 2},
            },
            {
                "name": "Active Warming",
                "stage_min": 30,
                "stage_max": 60,
                "actions_per_hour": 10,
                "session_duration_min": 45,
                "rest_between_sessions_hours": 6,
                "max_sessions_per_day": 3,
                "allowed_actions": ["read", "react", "view_profile", "subscribe"],
                "action_weights_override": {
                    "read": 4,
                    "react": 3,
                    "subscribe": 2,
                    "view_profile": 1,
                },
            },
            {
                "name": "Mature Warming",
                "stage_min": 60,
                "stage_max": 85,
                "actions_per_hour": 15,
                "session_duration_min": 60,
                "rest_between_sessions_hours": 4,
                "max_sessions_per_day": 4,
                "allowed_actions": [
                    "read",
                    "react",
                    "subscribe",
                    "view_profile",
                    "comment",
                ],
                "action_weights_override": {
                    "read": 3,
                    "react": 3,
                    "subscribe": 2,
                    "comment": 1,
                    "view_profile": 1,
                },
            },
            {
                "name": "Ready",
                "stage_min": 85,
                "stage_max": 100,
                "actions_per_hour": 0,
                "session_duration_min": 0,
                "rest_between_sessions_hours": 0,
                "max_sessions_per_day": 0,
                "allowed_actions": [],
                "action_weights_override": {},
            },
        ],
    )

    # Delay ranges per action (JSON: {"read": {"min": 5, "max": 30}, "react": {"min": 10, "max": 60}})
    delay_ranges: Mapped[dict] = mapped_column(
        JSON,
        default=lambda: {
            "read": {"min": 5, "max": 30},
            "react": {"min": 10, "max": 60},
            "view_profile": {"min": 3, "max": 15},
            "subscribe": {"min": 20, "max": 120},
            "comment": {"min": 30, "max": 300},
        },
    )

    # Anti-detection settings
    idle_probability: Mapped[float] = mapped_column(Float, default=0.15)
    idle_duration_min: Mapped[int] = mapped_column(Integer, default=60)
    idle_duration_max: Mapped[int] = mapped_column(Integer, default=300)
    action_order_randomization: Mapped[bool] = mapped_column(Boolean, default=True)
    interleave_non_target_actions: Mapped[bool] = mapped_column(Boolean, default=True)
    typing_speed_variation: Mapped[bool] = mapped_column(Boolean, default=True)

    # Channel pools for warming (JSON: list of channel usernames)
    warming_channels: Mapped[dict] = mapped_column(
        JSON, default=lambda: ["telegram", "durov"]
    )

    # Promotion settings
    stage_advance_probability: Mapped[float] = mapped_column(Float, default=0.3)
    max_stage_advance_per_session: Mapped[int] = mapped_column(Integer, default=5)
