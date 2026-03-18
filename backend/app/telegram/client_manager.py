import asyncio
from datetime import datetime, timedelta
from typing import Optional
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError, AuthKeyError, SessionPasswordNeededError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.logging import logger
from app.core.security import decrypt, encrypt
from app.models.account import Account, AccountStatus


class ClientManager:
    """Manages Telegram client connections with pooling and flood handling."""

    def __init__(self):
        self._clients: dict[str, TelegramClient] = {}
        self._flood_waits: dict[str, datetime] = {}
        self._max_concurrent = settings.MAX_CONCURRENT_WORKERS
        self._semaphore = asyncio.Semaphore(self._max_concurrent)
        self._lock = asyncio.Lock()

    async def get_client(self, account: Account) -> Optional[TelegramClient]:
        """Get or create a Telegram client for an account."""
        if not account.session_string:
            logger.error("No session string", account_id=account.id)
            return None

        if account.id in self._flood_waits:
            wait_until = self._flood_waits[account.id]
            if datetime.utcnow() < wait_until:
                logger.warning(
                    "Account in flood wait", account_id=account.id, until=wait_until
                )
                return None
            del self._flood_waits[account.id]

        async with self._lock:
            if account.id in self._clients:
                client = self._clients[account.id]
                if client.is_connected():
                    return client

        try:
            session_str = decrypt(account.session_string)
            client = TelegramClient(
                StringSession(session_str),
                settings.TELEGRAM_API_ID,
                settings.TELEGRAM_API_HASH,
                connection_retries=3,
                retry_delay=1,
                timeout=30,
            )
            await client.connect()

            me = await client.get_me()
            if not me:
                logger.error("Failed to validate session", account_id=account.id)
                await client.disconnect()
                return None

            async with self._lock:
                self._clients[account.id] = client

            logger.info("Client connected", account_id=account.id, user_id=me.id)
            return client

        except AuthKeyError:
            logger.error("Invalid auth key", account_id=account.id)
            return None
        except Exception as e:
            logger.error("Failed to connect", account_id=account.id, error=str(e))
            return None

    async def release_client(self, account_id: str, keep_alive: bool = True):
        """Release client back to pool or disconnect."""
        if not keep_alive:
            async with self._lock:
                client = self._clients.pop(account_id, None)
                if client:
                    await client.disconnect()

    async def handle_flood_wait(self, account_id: str, wait_seconds: int):
        """Handle FloodWaitError for an account."""
        wait_until = datetime.utcnow() + timedelta(seconds=wait_seconds + 10)
        self._flood_waits[account_id] = wait_until
        logger.warning(
            "Flood wait applied",
            account_id=account_id,
            wait_seconds=wait_seconds,
            until=wait_until,
        )

    async def disconnect_all(self):
        """Disconnect all clients."""
        async with self._lock:
            for account_id, client in self._clients.items():
                try:
                    await client.disconnect()
                except Exception:
                    pass
            self._clients.clear()

    async def active_count(self) -> int:
        async with self._lock:
            return sum(1 for c in self._clients.values() if c.is_connected())


client_manager = ClientManager()
