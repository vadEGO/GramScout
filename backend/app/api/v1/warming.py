from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.warming_service import warming_service, WarmingService


router = APIRouter(prefix="/warming", tags=["warming"])


@router.post("/start")
async def start_warming(db: AsyncSession = Depends(get_db)):
    await warming_service.start(db)
    return {"status": "started"}


@router.post("/stop")
async def stop_warming():
    await warming_service.stop()
    return {"status": "stopped"}


@router.post("/accounts")
async def warm_accounts(
    account_ids: list[str],
    db: AsyncSession = Depends(get_db),
):
    await WarmingService.start_warming(db, account_ids)
    return {"warming": len(account_ids)}
