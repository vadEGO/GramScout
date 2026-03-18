from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.comment_service import comment_service


router = APIRouter(prefix="/commenting", tags=["commenting"])


@router.post("/start")
async def start_commenting(
    num_workers: int = 5,
    db: AsyncSession = Depends(get_db),
):
    await comment_service.start(db, num_workers=num_workers)
    return {"status": "started", "workers": num_workers}


@router.post("/stop")
async def stop_commenting():
    await comment_service.stop()
    return {"status": "stopped"}


@router.get("/queue")
async def get_queue_size():
    size = await comment_service.queue_size()
    return {"queue_size": size}


@router.post("/enqueue")
async def enqueue_comment(
    account_id: str,
    channel_username: str,
    post_id: int,
    post_text: str,
):
    await comment_service.enqueue_comment(
        account_id=account_id,
        channel_username=channel_username,
        post_id=post_id,
        post_text=post_text,
    )
    return {"enqueued": True}
