from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.services.proxy_service import ProxyService


router = APIRouter(prefix="/proxies", tags=["proxies"])


@router.get("")
async def list_proxies(
    active_only: bool = True,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    proxies = await ProxyService.get_all(db, active_only=active_only, limit=limit)
    return [
        {
            "id": p.id,
            "ip": p.ip,
            "port": p.port,
            "country": p.country,
            "provider": p.provider,
            "protocol": p.protocol,
            "is_active": p.is_active,
            "ban_rate": p.ban_rate,
        }
        for p in proxies
    ]


@router.post("")
async def create_proxy(
    ip: str,
    port: int,
    username: str,
    password: str,
    country: str,
    provider: str,
    db: AsyncSession = Depends(get_db),
):
    proxy = await ProxyService.create(
        db,
        ip=ip,
        port=port,
        username=username,
        password=password,
        country=country,
        provider=provider,
    )
    return {"id": proxy.id, "ip": proxy.ip, "port": proxy.port}


@router.delete("/{proxy_id}")
async def delete_proxy(proxy_id: str, db: AsyncSession = Depends(get_db)):
    success = await ProxyService.delete(db, proxy_id)
    if not success:
        raise HTTPException(status_code=404, detail="Proxy not found")
    return {"deleted": True}
