from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import uuid

from app.core.database import get_db
from app.models.channel import Channel

router = APIRouter(prefix="/parser", tags=["parser"])


class ParsedUser:
    """In-memory store for parsed users (would be DB in production)."""

    pass


# In-memory parsing results storage
_parsing_results: dict[str, list] = {}
_parsing_status: dict[str, dict] = {}


@router.post("/users/parse-members")
async def start_member_parsing(
    channel_urls: str,
    account_ids: str = "",
    skip_bots: bool = True,
    skip_deleted: bool = True,
    skip_banned: bool = True,
    skip_scam: bool = True,
    only_active_days: int = 0,
    only_premium: bool = False,
    only_with_photo: bool = False,
    only_with_username: bool = False,
    ai_protection: bool = False,
    delay_min: int = 2,
    delay_max: int = 5,
):
    """Parse users from open member lists."""
    channels = [u.strip() for u in channel_urls.split(",") if u.strip()]
    parse_id = str(uuid.uuid4())[:8]

    _parsing_status[parse_id] = {
        "id": parse_id,
        "type": "members",
        "channels": channels,
        "status": "running",
        "filters": {
            "skip_bots": skip_bots,
            "skip_deleted": skip_deleted,
            "skip_banned": skip_banned,
            "skip_scam": skip_scam,
            "only_active_days": only_active_days,
            "only_premium": only_premium,
            "only_with_photo": only_with_photo,
            "only_with_username": only_with_username,
        },
        "ai_protection": ai_protection,
        "users_found": 0,
        "started_at": datetime.utcnow().isoformat(),
    }
    _parsing_results[parse_id] = []

    return {
        "parse_id": parse_id,
        "status": "started",
        "channels": len(channels),
        "note": "Parsing requires connected Telegram accounts. Results will appear in history.",
    }


@router.post("/users/parse-messages")
async def start_message_parsing(
    channel_urls: str,
    account_ids: str = "",
    message_limit: int = 1000,
    days_filter: int = 30,
    skip_bots: bool = True,
    skip_deleted: bool = True,
    skip_banned: bool = True,
    skip_scam: bool = True,
    only_with_username: bool = False,
    only_with_photo: bool = False,
    keyword_filter: str = "",
    quick_mode: bool = False,
    ai_protection: bool = False,
    delay_min: int = 2,
    delay_max: int = 5,
):
    """Parse users from messages (for closed member list chats)."""
    channels = [u.strip() for u in channel_urls.split(",") if u.strip()]
    keywords = (
        [k.strip() for k in keyword_filter.split(",") if k.strip()]
        if keyword_filter
        else []
    )
    parse_id = str(uuid.uuid4())[:8]

    _parsing_status[parse_id] = {
        "id": parse_id,
        "type": "messages",
        "channels": channels,
        "status": "running",
        "message_limit": message_limit,
        "days_filter": days_filter,
        "filters": {
            "skip_bots": skip_bots,
            "skip_deleted": skip_deleted,
            "skip_banned": skip_banned,
            "skip_scam": skip_scam,
            "only_with_username": only_with_username,
            "only_with_photo": only_with_photo,
        },
        "keyword_filter": keywords,
        "quick_mode": quick_mode,
        "ai_protection": ai_protection,
        "users_found": 0,
        "started_at": datetime.utcnow().isoformat(),
    }
    _parsing_results[parse_id] = []

    return {
        "parse_id": parse_id,
        "status": "started",
        "channels": len(channels),
        "keywords": keywords,
        "note": "Parsing requires connected Telegram accounts.",
    }


@router.get("/users/history")
async def get_parsing_history():
    """Get all parsing history."""
    return [
        {
            "id": s["id"],
            "type": s["type"],
            "status": s["status"],
            "channels": len(s["channels"]),
            "users_found": s.get("users_found", 0),
            "started_at": s.get("started_at"),
        }
        for s in _parsing_status.values()
    ]


@router.get("/users/results/{parse_id}")
async def get_parsing_results(parse_id: str):
    """Get results from a specific parsing run."""
    if parse_id not in _parsing_status:
        raise HTTPException(status_code=404, detail="Parse ID not found")
    return {
        "status": _parsing_status[parse_id]["status"],
        "users": _parsing_results.get(parse_id, []),
        "total": len(_parsing_results.get(parse_id, [])),
    }


@router.post("/channels/parse")
async def parse_channels(
    keywords: str,
    auto_suffixes: str = "news, chat, official, group",
    min_subscribers: int = 100,
    max_subscribers: int = 0,
    only_open_comments: bool = True,
    language: str = "auto",
    db: AsyncSession = Depends(get_db),
):
    """Parse channels by keywords (already implemented via channel parser)."""
    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
    suffix_list = [s.strip() for s in auto_suffixes.split(",") if s.strip()]

    return {
        "status": "started",
        "queries": len(keyword_list) * (len(suffix_list) + 1),
        "keywords": keyword_list,
        "suffixes": suffix_list,
        "note": "Use the Channel Parser UI for interactive parsing with live results.",
    }
