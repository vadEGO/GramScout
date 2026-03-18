import asyncio
import random
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.account import Account, AccountStatus
from app.models.action_log import ActionLog, ActionType, ActionResult
from app.telegram.account_actions import AccountActions


REACTION_EMOJIS = ["👍", "❤️", "🔥", "😂", "😮", "🎉", "👏", "💯"]


class ReactionService:
    """Mass reactions engine."""

    def __init__(self):
        self._running = False
        self._workers: list[asyncio.Task] = []

    async def start(self, db: AsyncSession, num_workers: int = 3):
        """Start reaction workers."""
        self._running = True
        for i in range(num_workers):
            task = asyncio.create_task(self._reaction_loop(db, f"reactor-{i}"))
            self._workers.append(task)
        logger.info("Reaction engine started", workers=num_workers)

    async def stop(self):
        """Stop reaction workers."""
        self._running = False
        for task in self._workers:
            task.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        logger.info("Reaction engine stopped")

    async def _reaction_loop(self, db: AsyncSession, worker_id: str):
        """Reaction worker loop."""
        while self._running:
            try:
                accounts = await self._get_available_accounts(db)
                if not accounts:
                    await asyncio.sleep(30)
                    continue

                for account in accounts[:5]:
                    if not self._running:
                        break
                    await self._react_to_channel(db, account, worker_id)
                    await asyncio.sleep(random.uniform(10, 60))

                await asyncio.sleep(random.uniform(60, 300))

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Reaction worker error", worker=worker_id, error=str(e))
                await asyncio.sleep(30)

    async def _get_available_accounts(self, db: AsyncSession) -> list[Account]:
        result = await db.execute(
            select(Account).where(
                Account.status.in_([AccountStatus.ACTIVE, AccountStatus.WORKING]),
                Account.warming_stage >= 50,
            )
        )
        return list(result.scalars().all())

    async def _react_to_channel(
        self, db: AsyncSession, account: Account, worker_id: str
    ):
        """React to recent posts in a target channel."""
        from app.models.channel import Channel

        result = await db.execute(
            select(Channel).where(Channel.is_target == True).limit(10)
        )
        channels = list(result.scalars().all())

        if not channels:
            return

        channel = random.choice(channels)
        emoji = random.choice(REACTION_EMOJIS)

        log = ActionLog(
            account_id=account.id,
            action_type=ActionType.REACT,
            target_channel=channel.url,
            content=emoji,
            delay_ms=random.randint(1000, 5000),
            result=ActionResult.SUCCESS,
        )
        db.add(log)

        account.last_active = datetime.utcnow()
        await db.commit()

        logger.info(
            "Reaction added",
            worker=worker_id,
            account=account.id,
            channel=channel.username,
            emoji=emoji,
        )


reaction_service = ReactionService()
