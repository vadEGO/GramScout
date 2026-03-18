from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.reaction_service import reaction_service


router = APIRouter(prefix="/reactions", tags=["reactions"])


@router.post("/start")
async def start_reactions(
    num_workers: int = 3,
    db: AsyncSession = Depends(get_db),
):
    await reaction_service.start(db, num_workers=num_workers)
    return {"status": "started", "workers": num_workers}


@router.post("/stop")
async def stop_reactions():
    await reaction_service.stop()
    return {"status": "stopped"}
