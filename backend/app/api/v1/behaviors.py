from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import uuid

from app.core.database import get_db
from app.models.behavior import (
    BehaviorProfile,
    AccountTrustScore,
    ChannelBlacklist,
    ChannelWhitelist,
    AccountTag,
    AccountTagAssignment,
    NeuroDialogueConfig,
    NeuroChatConfig,
    WarmingPreset,
)
from app.models.account import Account, AccountStatus

router = APIRouter(tags=["behavior"])


# ─── BEHAVIOR PROFILES ──────────────────────────────────────

BEHAVIOR_DEFAULTS = {
    "conservative": {
        "name": "Conservative",
        "profile_type": "conservative",
        "comments_per_day_max": 3,
        "reactions_per_day_max": 10,
        "reads_per_day_max": 50,
        "joins_per_day_max": 2,
        "dms_per_day_max": 5,
        "comment_delay_min": 120,
        "comment_delay_max": 600,
        "reaction_delay_min": 30,
        "reaction_delay_max": 120,
        "dm_delay_min": 180,
        "dm_delay_max": 900,
        "typing_speed_wpm": 35,
        "typing_speed_variation": 0.4,
        "read_before_comment_pct": 0.95,
        "scroll_before_action_pct": 0.8,
        "active_hours_start": 9,
        "active_hours_end": 21,
        "idle_probability": 0.25,
        "max_actions_per_session": 20,
        "session_duration_max_min": 60,
        "warming_intensity_base": 30,
        "trust_gain_per_clean_day": 2,
    },
    "moderate": {
        "name": "Moderate",
        "profile_type": "moderate",
        "comments_per_day_max": 10,
        "reactions_per_day_max": 30,
        "reads_per_day_max": 100,
        "joins_per_day_max": 5,
        "dms_per_day_max": 15,
        "comment_delay_min": 30,
        "comment_delay_max": 300,
        "reaction_delay_min": 10,
        "reaction_delay_max": 60,
        "dm_delay_min": 60,
        "dm_delay_max": 600,
        "typing_speed_wpm": 45,
        "typing_speed_variation": 0.3,
        "read_before_comment_pct": 0.8,
        "scroll_before_action_pct": 0.6,
        "active_hours_start": 8,
        "active_hours_end": 23,
        "idle_probability": 0.15,
        "max_actions_per_session": 50,
        "session_duration_max_min": 120,
        "warming_intensity_base": 50,
        "trust_gain_per_clean_day": 1,
    },
    "aggressive": {
        "name": "Aggressive",
        "profile_type": "aggressive",
        "comments_per_day_max": 25,
        "reactions_per_day_max": 80,
        "reads_per_day_max": 200,
        "joins_per_day_max": 10,
        "dms_per_day_max": 40,
        "comment_delay_min": 15,
        "comment_delay_max": 120,
        "reaction_delay_min": 5,
        "reaction_delay_max": 30,
        "dm_delay_min": 30,
        "dm_delay_max": 300,
        "typing_speed_wpm": 55,
        "typing_speed_variation": 0.2,
        "read_before_comment_pct": 0.5,
        "scroll_before_action_pct": 0.3,
        "active_hours_start": 7,
        "active_hours_end": 24,
        "idle_probability": 0.08,
        "max_actions_per_session": 100,
        "session_duration_max_min": 240,
        "warming_intensity_base": 80,
        "trust_gain_per_clean_day": 1,
    },
}


@router.get("/behaviors")
async def list_behaviors(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BehaviorProfile))
    profiles = list(result.scalars().all())
    if not profiles:
        # Create defaults
        for key, data in BEHAVIOR_DEFAULTS.items():
            p = BehaviorProfile(
                id=str(uuid.uuid4()), **data, is_default=(key == "moderate")
            )
            db.add(p)
        await db.commit()
        result = await db.execute(select(BehaviorProfile))
        profiles = list(result.scalars().all())
    return [
        {
            "id": p.id,
            "name": p.name,
            "type": p.profile_type,
            "comments_per_day": p.comments_per_day_max,
            "reactions_per_day": p.reactions_per_day_max,
            "is_default": p.is_default,
        }
        for p in profiles
    ]


@router.get("/behaviors/{profile_id}")
async def get_behavior(profile_id: str, db: AsyncSession = Depends(get_db)):
    p = await db.get(BehaviorProfile, profile_id)
    if not p:
        raise HTTPException(status_code=404, detail="Not found")
    return {k: v for k, v in p.__dict__.items() if not k.startswith("_")}


# ─── TRUST SCORES ────────────────────────────────────────────


@router.get("/trust/{account_id}")
async def get_trust_score(account_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AccountTrustScore).where(AccountTrustScore.account_id == account_id)
    )
    score = result.scalar_one_or_none()
    if not score:
        # Create default
        score = AccountTrustScore(id=str(uuid.uuid4()), account_id=account_id)
        db.add(score)
        await db.commit()
    return {
        "account_id": score.account_id,
        "score": score.score,
        "health_status": score.health_status,
        "total_mutes": score.total_mutes,
        "total_bans": score.total_bans,
        "total_clean_days": score.total_clean_days,
        "notes": score.notes,
    }


@router.get("/trust")
async def list_trust_scores(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AccountTrustScore).order_by(AccountTrustScore.score.desc())
    )
    return [
        {
            "account_id": s.account_id,
            "score": s.score,
            "health": s.health_status,
            "mutes": s.total_mutes,
            "bans": s.total_bans,
            "clean_days": s.total_clean_days,
        }
        for s in result.scalars().all()
    ]


# ─── BULK OPERATIONS ────────────────────────────────────────


@router.post("/bulk/leave-all-chats")
async def bulk_leave_chats(
    account_ids: str = Query(..., description="Comma-separated account IDs"),
    db: AsyncSession = Depends(get_db),
):
    """Leave all chats for selected accounts."""
    ids = [i.strip() for i in account_ids.split(",")]
    results = []
    for acc_id in ids:
        account = await db.get(Account, acc_id)
        if account:
            results.append(
                {
                    "account_id": acc_id,
                    "phone": account.phone,
                    "action": "leave_all_chats",
                    "status": "queued",
                }
            )
    return {"queued": len(results), "accounts": results}


@router.post("/bulk/unsubscribe-all")
async def bulk_unsubscribe(
    account_ids: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Unsubscribe from all channels."""
    ids = [i.strip() for i in account_ids.split(",")]
    return {"queued": len(ids), "action": "unsubscribe_all"}


@router.post("/bulk/read-all")
async def bulk_read_messages(
    account_ids: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Mark all messages as read."""
    ids = [i.strip() for i in account_ids.split(",")]
    return {"queued": len(ids), "action": "read_all_messages"}


@router.post("/bulk/terminate-sessions")
async def bulk_terminate_sessions(
    account_ids: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Terminate all other sessions (kick everyone except current)."""
    ids = [i.strip() for i in account_ids.split(",")]
    return {"queued": len(ids), "action": "terminate_sessions"}


@router.post("/bulk/set-2fa")
async def bulk_set_2fa(
    account_ids: str = Query(...),
    password: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Set 2FA on all selected accounts."""
    ids = [i.strip() for i in account_ids.split(",")]
    return {"queued": len(ids), "action": "set_2fa"}


@router.post("/bulk/clear-cache")
async def bulk_clear_cache(
    account_ids: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Clear Telegram cache for accounts."""
    ids = [i.strip() for i in account_ids.split(",")]
    return {"queued": len(ids), "action": "clear_cache"}


@router.post("/bulk/profile-update")
async def bulk_profile_update(
    account_ids: str = Query(...),
    first_name: str = "",
    last_name: str = "",
    bio: str = "",
    db: AsyncSession = Depends(get_db),
):
    """Bulk update profile names/bio."""
    ids = [i.strip() for i in account_ids.split(",")]
    return {
        "queued": len(ids),
        "action": "profile_update",
        "name": f"{first_name} {last_name}".strip(),
    }


# ─── TAGS / ROLES ───────────────────────────────────────────


@router.get("/tags")
async def list_tags(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AccountTag))
    return [
        {"id": t.id, "name": t.name, "color": t.color, "description": t.description}
        for t in result.scalars().all()
    ]


@router.post("/tags")
async def create_tag(
    name: str,
    color: str = "#3b82f6",
    description: str = "",
    db: AsyncSession = Depends(get_db),
):
    tag = AccountTag(
        id=str(uuid.uuid4()), name=name, color=color, description=description
    )
    db.add(tag)
    await db.commit()
    return {"id": tag.id, "name": tag.name}


@router.post("/tags/assign")
async def assign_tag(account_id: str, tag_id: str, db: AsyncSession = Depends(get_db)):
    assignment = AccountTagAssignment(
        id=str(uuid.uuid4()), account_id=account_id, tag_id=tag_id
    )
    db.add(assignment)
    await db.commit()
    return {"assigned": True}


# ─── BLACKLIST / WHITELIST ──────────────────────────────────


@router.get("/blacklist")
async def get_blacklist(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ChannelBlacklist).order_by(ChannelBlacklist.added_at.desc())
    )
    return [
        {
            "id": b.id,
            "channel": b.channel_url,
            "reason": b.reason,
            "account_id": b.account_id,
            "added_at": b.added_at.isoformat(),
        }
        for b in result.scalars().all()
    ]


@router.post("/blacklist")
async def add_to_blacklist(
    channel_url: str,
    reason: str = "manual",
    account_id: str = "",
    db: AsyncSession = Depends(get_db),
):
    entry = ChannelBlacklist(
        id=str(uuid.uuid4()),
        channel_url=channel_url,
        reason=reason,
        account_id=account_id or None,
    )
    db.add(entry)
    await db.commit()
    return {"added": True}


@router.get("/whitelist")
async def get_whitelist(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ChannelWhitelist).order_by(ChannelWhitelist.success_count.desc())
    )
    return [
        {
            "id": w.id,
            "channel": w.channel_url,
            "successes": w.success_count,
            "last_success": w.last_success.isoformat(),
        }
        for w in result.scalars().all()
    ]


# ─── NEURODIALOGUE (DM AUTO-REPLY) ──────────────────────────


@router.get("/neurodialogue/configs")
async def list_dialogue_configs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(NeuroDialogueConfig).where(NeuroDialogueConfig.is_active == True)
    )
    return [
        {
            "id": c.id,
            "name": c.name,
            "prompt_preview": c.system_prompt[:100],
            "product": c.product_name,
            "reply_delay": f"{c.reply_delay_min}-{c.reply_delay_max}s",
        }
        for c in result.scalars().all()
    ]


@router.post("/neurodialogue/configs")
async def create_dialogue_config(
    name: str,
    system_prompt: str,
    context_message_count: int = 10,
    reply_delay_min: int = 5,
    reply_delay_max: int = 60,
    max_reply_length: int = 200,
    product_name: str = "",
    product_url: str = "",
    organic_promotion_pct: int = 15,
    db: AsyncSession = Depends(get_db),
):
    config = NeuroDialogueConfig(
        id=str(uuid.uuid4()),
        name=name,
        system_prompt=system_prompt,
        context_message_count=context_message_count,
        reply_delay_min=reply_delay_min,
        reply_delay_max=reply_delay_max,
        max_reply_length=max_reply_length,
        product_name=product_name or None,
        product_url=product_url or None,
        organic_promotion_pct=organic_promotion_pct,
    )
    db.add(config)
    await db.commit()
    return {"id": config.id, "name": config.name}


# ─── NEUROCHAT (GROUP MONITORING) ────────────────────────────


@router.get("/neurochat/configs")
async def list_chat_configs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NeuroChatConfig))
    return [
        {
            "id": c.id,
            "name": c.name,
            "mode": c.mode,
            "active": c.is_active,
            "keywords": c.trigger_keywords,
            "groups": len(c.target_group_urls or []),
        }
        for c in result.scalars().all()
    ]


@router.post("/neurochat/configs")
async def create_chat_config(
    name: str,
    mode: str = "trigger",
    trigger_keywords: str = "",
    semantic_matching: bool = True,
    reply_interval_pct: int = 50,
    system_prompt: str = "",
    target_group_urls: str = "",
    language: str = "auto",
    context_window: int = 15,
    ai_protection: bool = True,
    protection_mode: str = "balanced",
    max_messages: int = 500,
    messages_before_switch: int = 10,
    delay_min: int = 5,
    delay_max: int = 60,
    organic_promotion: bool = False,
    organic_promotion_pct: int = 15,
    product_name: str = "",
    db: AsyncSession = Depends(get_db),
):
    config = NeuroChatConfig(
        id=str(uuid.uuid4()),
        name=name,
        mode=mode,
        trigger_keywords=[k.strip() for k in trigger_keywords.split(",") if k.strip()]
        if trigger_keywords
        else [],
        semantic_matching=semantic_matching,
        reply_interval_pct=reply_interval_pct,
        system_prompt=system_prompt,
        target_group_urls=[
            u.strip() for u in target_group_urls.split(",") if u.strip()
        ],
        language=language,
        context_window=context_window,
        ai_protection_enabled=ai_protection,
        protection_mode=protection_mode,
        max_messages_per_session=max_messages,
        messages_before_account_switch=messages_before_switch,
        delay_min=delay_min,
        delay_max=delay_max,
        organic_promotion_enabled=organic_promotion,
        organic_promotion_pct=organic_promotion_pct,
    )
    db.add(config)
    await db.commit()
    return {"id": config.id, "name": config.name}


# ─── WARMING PRESETS ────────────────────────────────────────


@router.get("/warming-presets")
async def list_warming_presets(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WarmingPreset))
    return [
        {
            "id": p.id,
            "name": p.name,
            "intensity": p.intensity,
            "duration": p.session_duration_min,
            "actions": p.actions,
        }
        for p in result.scalars().all()
    ]


@router.post("/warming-presets")
async def create_warming_preset(
    name: str,
    intensity: str = "normal",
    session_duration_min: int = 30,
    actions: str = "reactions,reading",
    channel_urls: str = "",
    schedule_start: int = 0,
    schedule_end: int = 24,
    db: AsyncSession = Depends(get_db),
):
    action_list = [a.strip() for a in actions.split(",")]
    preset = WarmingPreset(
        id=str(uuid.uuid4()),
        name=name,
        intensity=intensity,
        session_duration_min=session_duration_min,
        actions={a: True for a in action_list},
        channel_urls=[u.strip() for u in channel_urls.split(",") if u.strip()],
        safety_limits={
            "actions_per_hour": 20,
            "actions_per_day": 100,
            "joins_per_day": 5,
            "messages_per_day": 20,
        },
        schedule_start=schedule_start,
        schedule_end=schedule_end,
    )
    db.add(preset)
    await db.commit()
    return {"id": preset.id, "name": preset.name}
