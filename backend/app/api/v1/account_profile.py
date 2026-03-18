from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.database import get_db
from app.models.account import Account, AccountStatus
from app.models.channel import Channel
from app.models.account_target import AccountChannelTarget
from app.telegram.client_manager import client_manager

router = APIRouter(prefix="/accounts", tags=["accounts-profile"])


# ─── TARGETING ───────────────────────────────────────────────


@router.get("/{account_id}/targets")
async def get_account_targets(account_id: str, db: AsyncSession = Depends(get_db)):
    """Get all channel targets for an account."""
    result = await db.execute(
        select(AccountChannelTarget, Channel)
        .join(Channel, AccountChannelTarget.channel_id == Channel.id)
        .where(AccountChannelTarget.account_id == account_id)
        .order_by(AccountChannelTarget.priority.asc())
    )
    rows = result.all()
    return [
        {
            "target_id": t.id,
            "channel_id": ch.id,
            "channel_name": ch.name,
            "channel_username": ch.username,
            "channel_url": ch.url,
            "subscribers": ch.subscribers,
            "priority": t.priority,
            "actions_per_day": t.actions_per_day,
            "comment_enabled": t.comment_enabled,
            "react_enabled": t.react_enabled,
            "subscribe_enabled": t.subscribe_enabled,
        }
        for t, ch in rows
    ]


@router.post("/{account_id}/targets")
async def assign_account_to_channel(
    account_id: str,
    channel_id: str,
    priority: int = 5,
    actions_per_day: int = 5,
    db: AsyncSession = Depends(get_db),
):
    """Assign an account to target a specific channel."""
    account = await db.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    channel = await db.get(Channel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    existing = await db.execute(
        select(AccountChannelTarget).where(
            AccountChannelTarget.account_id == account_id,
            AccountChannelTarget.channel_id == channel_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400, detail="Account already targeting this channel"
        )

    target = AccountChannelTarget(
        id=str(uuid.uuid4()),
        account_id=account_id,
        channel_id=channel_id,
        priority=priority,
        actions_per_day=actions_per_day,
    )
    db.add(target)
    await db.commit()
    return {"assigned": True, "account": account.phone, "channel": channel.name}


@router.delete("/{account_id}/targets/{target_id}")
async def remove_account_target(
    account_id: str, target_id: str, db: AsyncSession = Depends(get_db)
):
    """Remove an account from a channel target."""
    target = await db.get(AccountChannelTarget, target_id)
    if not target or target.account_id != account_id:
        raise HTTPException(status_code=404, detail="Target not found")
    await db.delete(target)
    await db.commit()
    return {"removed": True}


@router.patch("/{account_id}/targets/{target_id}")
async def update_target_settings(
    account_id: str,
    target_id: str,
    priority: int | None = None,
    actions_per_day: int | None = None,
    comment_enabled: bool | None = None,
    react_enabled: bool | None = None,
    subscribe_enabled: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Update targeting settings for an account-channel assignment."""
    target = await db.get(AccountChannelTarget, target_id)
    if not target or target.account_id != account_id:
        raise HTTPException(status_code=404, detail="Target not found")

    if priority is not None:
        target.priority = priority
    if actions_per_day is not None:
        target.actions_per_day = actions_per_day
    if comment_enabled is not None:
        target.comment_enabled = comment_enabled
    if react_enabled is not None:
        target.react_enabled = react_enabled
    if subscribe_enabled is not None:
        target.subscribe_enabled = subscribe_enabled

    await db.commit()
    return {"updated": True}


@router.post("/{account_id}/targets/bulk")
async def bulk_assign_channels(
    account_id: str,
    channel_ids: str = Query(..., description="Comma-separated channel IDs"),
    priority: int = 5,
    db: AsyncSession = Depends(get_db),
):
    """Assign an account to multiple channels at once."""
    ids = [cid.strip() for cid in channel_ids.split(",") if cid.strip()]
    assigned = 0
    for ch_id in ids:
        existing = await db.execute(
            select(AccountChannelTarget).where(
                AccountChannelTarget.account_id == account_id,
                AccountChannelTarget.channel_id == ch_id,
            )
        )
        if not existing.scalar_one_or_none():
            target = AccountChannelTarget(
                id=str(uuid.uuid4()),
                account_id=account_id,
                channel_id=ch_id,
                priority=priority,
            )
            db.add(target)
            assigned += 1
    await db.commit()
    return {"assigned": assigned, "total_requested": len(ids)}


@router.get("/by-channel/{channel_id}")
async def get_accounts_for_channel(channel_id: str, db: AsyncSession = Depends(get_db)):
    """Get all accounts targeting a specific channel."""
    result = await db.execute(
        select(AccountChannelTarget, Account)
        .join(Account, AccountChannelTarget.account_id == Account.id)
        .where(AccountChannelTarget.channel_id == channel_id)
        .order_by(AccountChannelTarget.priority.asc())
    )
    rows = result.all()
    return [
        {
            "target_id": t.id,
            "account_id": a.id,
            "phone": a.phone,
            "status": a.status.value,
            "warming_stage": a.warming_stage,
            "persona": a.persona,
            "priority": t.priority,
            "actions_per_day": t.actions_per_day,
        }
        for t, a in rows
    ]


# ─── PROFILE MANAGEMENT ──────────────────────────────────────


@router.get("/{account_id}/profile")
async def get_telegram_profile(account_id: str, db: AsyncSession = Depends(get_db)):
    """Fetch current Telegram profile for an account."""
    account = await db.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    client = await client_manager.get_client(account)
    if not client:
        raise HTTPException(status_code=400, detail="Cannot connect - no valid session")

    try:
        me = await client.get_me()
        return {
            "id": me.id,
            "username": me.username,
            "first_name": me.first_name,
            "last_name": me.last_name,
            "phone": me.phone,
            "bio": (await client.get_me(full=True)).about
            if hasattr(me, "about")
            else None,
            "is_premium": getattr(me, "premium", False),
            "profile_photos_count": (
                await client.get_profile_photos(me, limit=1)
            ).total,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch profile: {str(e)}"
        )


@router.put("/{account_id}/profile")
async def update_telegram_profile(
    account_id: str,
    first_name: str | None = None,
    last_name: str | None = None,
    bio: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Update Telegram profile (name, bio) for an account."""
    account = await db.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    client = await client_manager.get_client(account)
    if not client:
        raise HTTPException(status_code=400, detail="Cannot connect - no valid session")

    try:
        updates = {}
        if first_name is not None:
            await client(functions.account.UpdateProfileRequest(first_name=first_name))
            updates["first_name"] = first_name
        if last_name is not None:
            await client(functions.account.UpdateProfileRequest(last_name=last_name))
            updates["last_name"] = last_name
        if bio is not None:
            await client(functions.account.UpdateProfileRequest(about=bio))
            updates["bio"] = bio

        if first_name:
            account.first_name = first_name
        if last_name:
            account.last_name = last_name
        if bio:
            account.bio = bio
        await db.commit()

        return {"updated": True, "changes": updates}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update profile: {str(e)}"
        )


@router.post("/{account_id}/profile/photo")
async def upload_profile_photo(
    account_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a new profile photo for an account."""
    account = await db.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    client = await client_manager.get_client(account)
    if not client:
        raise HTTPException(status_code=400, detail="Cannot connect - no valid session")

    try:
        import tempfile, os

        contents = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        await client(
            functions.photos.UploadProfilePhotoRequest(
                file=await client.upload_file(tmp_path)
            )
        )
        os.unlink(tmp_path)

        return {"uploaded": True, "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload photo: {str(e)}")


@router.get("/{account_id}/session")
async def export_session(account_id: str, db: AsyncSession = Depends(get_db)):
    """Export session string for manual login."""
    account = await db.get(Account, account_id)
    if not account or not account.session_string:
        raise HTTPException(status_code=404, detail="No session found")

    from app.core.security import decrypt

    session_str = decrypt(account.session_string)
    return {
        "account_id": account_id,
        "phone": account.phone,
        "session_string": session_str,
        "note": "Use this with: from telethon.sessions import StringSession; client = TelegramClient(StringSession('...'), api_id, api_hash)",
    }


@router.post("/{account_id}/set-bio")
async def quick_set_bio(
    account_id: str,
    bio: str,
    db: AsyncSession = Depends(get_db),
):
    """Quick helper to set account bio with channel link."""
    account = await db.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    client = await client_manager.get_client(account)
    if not client:
        raise HTTPException(status_code=400, detail="Cannot connect - no valid session")

    try:
        await client(functions.account.UpdateProfileRequest(about=bio))
        account.bio = bio
        await db.commit()
        return {"updated": True, "bio": bio}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")


# Import telethon functions
from telethon.tl import functions
