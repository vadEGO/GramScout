import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.proxy import Proxy
from app.config import settings


class ProxyService:
    """Proxy management service."""

    @staticmethod
    async def create(
        db: AsyncSession,
        ip: str,
        port: int,
        username: str,
        password: str,
        country: str,
        provider: str,
        protocol: str = "SOCKS5",
    ) -> Proxy:
        proxy = Proxy(
            id=str(uuid.uuid4()),
            ip=ip,
            port=port,
            username=username,
            password=password,
            protocol=protocol,
            country=country,
            provider=provider,
            is_active=True,
        )
        db.add(proxy)
        await db.commit()
        await db.refresh(proxy)

        logger.info("Proxy created", proxy_id=proxy.id, ip=ip, provider=provider)
        return proxy

    @staticmethod
    async def get(db: AsyncSession, proxy_id: str) -> Optional[Proxy]:
        result = await db.execute(select(Proxy).where(Proxy.id == proxy_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        db: AsyncSession, active_only: bool = True, limit: int = 100
    ) -> list[Proxy]:
        query = select(Proxy).limit(limit)
        if active_only:
            query = query.where(Proxy.is_active == True)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_available_proxy(db: AsyncSession) -> Optional[Proxy]:
        """Get a proxy with available capacity."""
        from app.models.account import Account

        result = await db.execute(
            select(Proxy).where(Proxy.is_active == True).order_by(Proxy.ban_rate.asc())
        )
        proxies = list(result.scalars().all())

        for proxy in proxies:
            count_result = await db.execute(
                select(func.count(Account.id)).where(Account.proxy_id == proxy.id)
            )
            count = count_result.scalar()
            if count < settings.MAX_ACCOUNTS_PER_PROXY:
                return proxy

        return None

    @staticmethod
    async def assign_to_account(db: AsyncSession, account_id: str) -> Optional[Proxy]:
        """Assign an available proxy to an account."""
        proxy = await ProxyService.get_available_proxy(db)
        if proxy:
            from app.models.account import Account

            account = await db.execute(select(Account).where(Account.id == account_id))
            acc = account.scalar_one_or_none()
            if acc:
                acc.proxy_id = proxy.id
                await db.commit()
                logger.info("Proxy assigned", account_id=account_id, proxy_id=proxy.id)
        return proxy

    @staticmethod
    async def update_ban_rate(db: AsyncSession, proxy_id: str):
        """Recalculate proxy ban rate based on account bans."""
        from app.models.account import Account

        result = await db.execute(
            select(func.count(Account.id), func.sum(Account.ban_count)).where(
                Account.proxy_id == proxy_id
            )
        )
        row = result.one()
        total_accounts = row[0] or 0
        total_bans = row[1] or 0

        if total_accounts > 0:
            proxy = await ProxyService.get(db, proxy_id)
            if proxy:
                proxy.ban_rate = total_bans / total_accounts
                if proxy.ban_rate > 0.5:
                    proxy.is_active = False
                    logger.warning(
                        "Proxy disabled due to high ban rate",
                        proxy_id=proxy_id,
                        rate=proxy.ban_rate,
                    )
                await db.commit()

    @staticmethod
    async def delete(db: AsyncSession, proxy_id: str) -> bool:
        proxy = await ProxyService.get(db, proxy_id)
        if proxy:
            await db.delete(proxy)
            await db.commit()
            return True
        return False
