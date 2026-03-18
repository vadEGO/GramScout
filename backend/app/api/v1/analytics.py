from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.account import Account
from app.models.action_log import ActionLog, ActionType, ActionResult


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
async def dashboard(db: AsyncSession = Depends(get_db)):
    now = datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_accounts = (await db.execute(select(func.count(Account.id)))).scalar()
    active_accounts = (
        await db.execute(
            select(func.count(Account.id)).where(
                Account.status.in_(["active", "working"])
            )
        )
    ).scalar()
    banned_accounts = (
        await db.execute(
            select(func.count(Account.id)).where(Account.status == "banned")
        )
    ).scalar()

    comments_today = (
        await db.execute(
            select(func.count(ActionLog.id)).where(
                ActionLog.action_type == ActionType.COMMENT,
                ActionLog.timestamp >= today,
            )
        )
    ).scalar()
    reactions_today = (
        await db.execute(
            select(func.count(ActionLog.id)).where(
                ActionLog.action_type == ActionType.REACT,
                ActionLog.timestamp >= today,
            )
        )
    ).scalar()

    return {
        "total_accounts": total_accounts,
        "active_accounts": active_accounts,
        "banned_accounts": banned_accounts,
        "comments_today": comments_today,
        "reactions_today": reactions_today,
        "timestamp": now.isoformat(),
    }


@router.get("/ban-rate")
async def ban_rate(db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count(Account.id)))).scalar()
    banned = (
        await db.execute(
            select(func.count(Account.id)).where(Account.status == "banned")
        )
    ).scalar()
    rate = (banned / total * 100) if total > 0 else 0
    return {"total_accounts": total, "banned": banned, "ban_rate_pct": round(rate, 2)}


@router.get("/actions")
async def action_stats(hours: int = 24, db: AsyncSession = Depends(get_db)):
    since = datetime.utcnow() - timedelta(hours=hours)
    result = await db.execute(
        select(ActionLog.action_type, func.count(ActionLog.id))
        .where(ActionLog.timestamp >= since)
        .group_by(ActionLog.action_type)
    )
    return {
        "period_hours": hours,
        "actions": {row[0].value: row[1] for row in result.all()},
    }
