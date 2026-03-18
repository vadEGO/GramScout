from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.models.account import AccountStatus, AccountFormat
from app.services.account_service import AccountService


router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("")
async def list_accounts(
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    account_status = AccountStatus(status) if status else None
    accounts = await AccountService.get_all(
        db, status=account_status, limit=limit, offset=offset
    )
    return [
        {
            "id": a.id,
            "phone": a.phone,
            "status": a.status.value,
            "persona": a.persona,
            "gender": a.gender,
            "warming_stage": a.warming_stage,
            "premium": a.premium,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "last_active": a.last_active.isoformat() if a.last_active else None,
        }
        for a in accounts
    ]


@router.get("/stats")
async def account_stats(db: AsyncSession = Depends(get_db)):
    counts = await AccountService.count_by_status(db)
    return {"by_status": counts, "total": sum(counts.values())}


@router.get("/{account_id}")
async def get_account(account_id: str, db: AsyncSession = Depends(get_db)):
    account = await AccountService.get(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return {
        "id": account.id,
        "phone": account.phone,
        "status": account.status.value,
        "persona": account.persona,
        "warming_stage": account.warming_stage,
        "premium": account.premium,
        "username": account.username,
        "first_name": account.first_name,
        "ban_count": account.ban_count,
        "assigned_model": account.assigned_model,
    }


@router.post("")
async def create_account(
    phone: str,
    country_code: str,
    session_string: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    account = await AccountService.create(
        db, phone=phone, country_code=country_code, session_string=session_string
    )
    return {"id": account.id, "phone": account.phone, "status": account.status.value}


@router.patch("/{account_id}/status")
async def update_status(
    account_id: str, status: str, db: AsyncSession = Depends(get_db)
):
    account = await AccountService.update_status(db, account_id, AccountStatus(status))
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"id": account.id, "status": account.status.value}


@router.delete("/{account_id}")
async def delete_account(account_id: str, db: AsyncSession = Depends(get_db)):
    success = await AccountService.delete(db, account_id)
    if not success:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"deleted": True}


@router.put("/{account_id}")
async def update_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    first_name: str | None = None,
    last_name: str | None = None,
    username: str | None = None,
    bio: str | None = None,
    gender: str | None = None,
    assigned_model: str | None = None,
    persona_type: str | None = None,
):
    """Update account properties including persona."""
    account = await AccountService.get(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if first_name is not None:
        account.first_name = first_name
    if last_name is not None:
        account.last_name = last_name
    if username is not None:
        account.username = username
    if bio is not None:
        account.bio = bio
    if gender is not None:
        account.gender = gender
    if assigned_model is not None:
        account.assigned_model = assigned_model
    if persona_type is not None and account.persona:
        account.persona = {**account.persona, "personality_type": persona_type}

    await db.commit()
    await db.refresh(account)
    return {
        "id": account.id,
        "phone": account.phone,
        "first_name": account.first_name,
        "last_name": account.last_name,
        "gender": account.gender,
        "persona": account.persona,
        "assigned_model": account.assigned_model,
    }
