from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.models.channel import Channel


router = APIRouter(prefix="/channels", tags=["channels"])


@router.get("")
async def list_channels(
    is_target: Optional[bool] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    query = select(Channel).limit(limit)
    if is_target is not None:
        query = query.where(Channel.is_target == is_target)
    result = await db.execute(query.order_by(Channel.quality_score.desc()))
    channels = list(result.scalars().all())
    return [
        {
            "id": c.id,
            "url": c.url,
            "name": c.name,
            "username": c.username,
            "subscribers": c.subscribers,
            "is_target": c.is_target,
            "open_comments": c.open_comments,
            "quality_score": c.quality_score,
            "topic": c.topic,
        }
        for c in channels
    ]


@router.post("")
async def create_channel(
    url: str,
    name: str,
    username: Optional[str] = None,
    subscribers: int = 0,
    is_target: bool = False,
    db: AsyncSession = Depends(get_db),
):
    import uuid

    channel = Channel(
        id=str(uuid.uuid4()),
        url=url,
        name=name,
        username=username,
        subscribers=subscribers,
        is_target=is_target,
    )
    db.add(channel)
    await db.commit()
    return {"id": channel.id, "name": channel.name}


@router.patch("/{channel_id}/target")
async def set_target(
    channel_id: str, is_target: bool, db: AsyncSession = Depends(get_db)
):
    channel = await db.get(Channel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    channel.is_target = is_target
    await db.commit()
    return {"id": channel.id, "is_target": channel.is_target}
