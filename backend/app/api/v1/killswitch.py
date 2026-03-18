from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import uuid

from app.core.database import get_db
from app.core.logging import logger
from app.models.account import Account, AccountStatus

router = APIRouter(prefix="/killswitch", tags=["killswitch"])


@router.post("/emergency-stop")
async def emergency_stop(
    reason: str = "Manual emergency stop",
    db: AsyncSession = Depends(get_db),
):
    """Emergency stop: pause all engines and quarantine all active accounts."""
    result = await db.execute(
        select(Account).where(
            Account.status.in_([AccountStatus.ACTIVE, AccountStatus.WORKING])
        )
    )
    accounts = list(result.scalars().all())

    for acc in accounts:
        acc.status = AccountStatus.MUTED
    await db.commit()

    logger.critical("EMERGENCY STOP", reason=reason, accounts_affected=len(accounts))
    return {
        "stopped": True,
        "reason": reason,
        "accounts_paused": len(accounts),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/kill-account")
async def kill_account(
    account_id: str,
    reason: str = "Manual kill",
    terminate_sessions: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """Kill a specific account: mute, terminate sessions, disconnect."""
    account = await db.get(Account, account_id)
    if not account:
        raise HTTPException(404, "Account not found")

    old_status = account.status
    account.status = AccountStatus.MUTED
    account.last_active = datetime.utcnow()
    await db.commit()

    logger.warning(
        "Account killed",
        account_id=account_id,
        phone=account.phone,
        reason=reason,
        was=old_status.value,
    )
    return {
        "killed": True,
        "account_id": account_id,
        "phone": account.phone,
        "previous_status": old_status.value,
        "terminate_sessions": terminate_sessions,
    }


@router.post("/quarantine")
async def quarantine_accounts(
    account_ids: str = Query(..., description="Comma-separated account IDs"),
    db: AsyncSession = Depends(get_db),
):
    """Put accounts into quarantine (muted state for review)."""
    ids = [i.strip() for i in account_ids.split(",")]
    quarantined = 0
    for acc_id in ids:
        account = await db.get(Account, acc_id)
        if account and account.status != AccountStatus.BANNED:
            account.status = AccountStatus.MUTED
            quarantined += 1
    await db.commit()
    logger.info("Accounts quarantined", count=quarantined)
    return {"quarantined": quarantined, "total_requested": len(ids)}


@router.post("/cleanup-banned")
async def cleanup_banned(db: AsyncSession = Depends(get_db)):
    """Remove all permanently banned accounts from the database."""
    result = await db.execute(
        select(Account).where(
            Account.status == AccountStatus.BANNED, Account.ban_count >= 3
        )
    )
    banned = list(result.scalars().all())
    count = len(banned)
    for acc in banned:
        await db.delete(acc)
    await db.commit()
    logger.info("Banned accounts cleaned up", count=count)
    return {"deleted": count, "message": f"Removed {count} permanently banned accounts"}


@router.post("/cleanup-stale")
async def cleanup_stale(
    days_inactive: int = 30,
    db: AsyncSession = Depends(get_db),
):
    """Remove accounts that have been muted/quarantined for too long."""
    cutoff = datetime.utcnow() - timedelta(days=days_inactive)
    result = await db.execute(
        select(Account).where(
            Account.status == AccountStatus.MUTED,
            Account.last_active < cutoff,
        )
    )
    stale = list(result.scalars().all())
    count = len(stale)
    for acc in stale:
        await db.delete(acc)
    await db.commit()
    logger.info("Stale accounts cleaned up", count=count, days=days_inactive)
    return {"deleted": count, "cutoff_days": days_inactive}


@router.post("/restart-account")
async def restart_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Restart a muted/quarantined account back to active."""
    account = await db.get(Account, account_id)
    if not account:
        raise HTTPException(404, "Account not found")
    if account.status == AccountStatus.BANNED:
        raise HTTPException(400, "Cannot restart a banned account")
    account.status = AccountStatus.ACTIVE
    account.last_active = datetime.utcnow()
    await db.commit()
    logger.info("Account restarted", account_id=account_id, phone=account.phone)
    return {"restarted": True, "account_id": account_id, "status": "active"}


@router.post("/bulk-restart")
async def bulk_restart(
    from_status: str = "muted",
    db: AsyncSession = Depends(get_db),
):
    """Bulk restart all accounts with a given status back to active."""
    try:
        status = AccountStatus(from_status)
    except ValueError:
        raise HTTPException(400, f"Invalid status: {from_status}")

    result = await db.execute(select(Account).where(Account.status == status))
    accounts = list(result.scalars().all())
    for acc in accounts:
        acc.status = AccountStatus.ACTIVE
        acc.last_active = datetime.utcnow()
    await db.commit()
    logger.info("Bulk restart", count=len(accounts), from_status=from_status)
    return {"restarted": len(accounts)}


@router.get("/status")
async def killswitch_status(db: AsyncSession = Depends(get_db)):
    """Get current account status breakdown for monitoring."""
    result = await db.execute(
        select(Account.status, func.count(Account.id)).group_by(Account.status)
    )
    counts = {row[0].value: row[1] for row in result.all()}

    # Calculate risk indicators
    total = sum(counts.values())
    banned_pct = round((counts.get("banned", 0) / max(total, 1)) * 100, 1)
    muted_pct = round((counts.get("muted", 0) / max(total, 1)) * 100, 1)

    risk_level = "LOW"
    if banned_pct > 10:
        risk_level = "HIGH"
    elif banned_pct > 5:
        risk_level = "MEDIUM"

    return {
        "counts": counts,
        "total": total,
        "banned_pct": banned_pct,
        "muted_pct": muted_pct,
        "risk_level": risk_level,
        "needs_attention": counts.get("banned", 0) > 0 or counts.get("muted", 0) > 0,
    }


# Import needed
from datetime import timedelta
