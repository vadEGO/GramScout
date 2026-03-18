import asyncio
import random
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.logging import logger
from app.models.account import Account, AccountStatus
from app.models.action_log import ActionLog, ActionType, ActionResult


WARMING_CHANNELS = [
    "telegram",
    "durov",
    "news",
]


class WarmingService:
    """Account warming engine - simulates human behavior to build trust."""

    def __init__(self):
        self._running = False
        self._warmers: list[asyncio.Task] = []

    async def start(self, db: AsyncSession):
        """Start warming loop."""
        self._running = True
        task = asyncio.create_task(self._warming_loop(db))
        self._warmers.append(task)
        logger.info("Warming engine started")

    async def stop(self):
        """Stop warming."""
        self._running = False
        for task in self._warmers:
            task.cancel()
        await asyncio.gather(*self._warmers, return_exceptions=True)
        self._warmers.clear()
        logger.info("Warming engine stopped")

    async def _warming_loop(self, db: AsyncSession):
        """Main warming loop - checks for accounts that need warming."""
        while self._running:
            try:
                accounts = await self._get_accounts_to_warm(db)
                for account in accounts:
                    await self._warm_account(db, account)
                await asyncio.sleep(300)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Warming loop error", error=str(e))
                await asyncio.sleep(60)

    async def _get_accounts_to_warm(self, db: AsyncSession) -> list[Account]:
        """Get accounts that need warming."""
        result = await db.execute(
            select(Account).where(
                Account.status == AccountStatus.WARMING,
                Account.warming_stage < 100,
            )
        )
        return list(result.scalars().all())

    async def _warm_account(self, db: AsyncSession, account: Account):
        """Perform a warming session for an account."""
        stage = account.warming_stage
        actions_per_hour = self._get_actions_per_hour(stage)

        logger.info(
            "Warming account",
            account_id=account.id,
            stage=stage,
            actions_per_hour=actions_per_hour,
        )

        actions_done = 0
        session_duration = random.randint(
            settings.WARMING_SESSION_DURATION_MIN,
            settings.WARMING_SESSION_DURATION_MIN * 2,
        )
        end_time = datetime.utcnow() + timedelta(minutes=session_duration)

        while datetime.utcnow() < end_time and actions_done < actions_per_hour:
            action_type = self._pick_action(stage)

            log = ActionLog(
                account_id=account.id,
                action_type=action_type,
                target_channel=random.choice(WARMING_CHANNELS),
                delay_ms=random.randint(2000, 30000),
                result=ActionResult.SUCCESS,
            )
            db.add(log)
            actions_done += 1

            delay = random.uniform(30, 120)
            await asyncio.sleep(delay)

        account.warming_stage = min(100, stage + random.randint(1, 5))
        account.last_active = datetime.utcnow()

        if account.warming_stage >= 80:
            account.status = AccountStatus.ACTIVE
            logger.info("Account fully warmed", account_id=account.id)

        await db.commit()

    def _get_actions_per_hour(self, stage: int) -> int:
        """Get actions per hour based on warming stage."""
        if stage < 10:
            return random.randint(3, 5)
        elif stage < 30:
            return random.randint(5, 10)
        elif stage < 60:
            return random.randint(10, 15)
        else:
            return random.randint(15, 20)

    def _pick_action(self, stage: int) -> ActionType:
        """Pick a warming action based on stage."""
        if stage < 20:
            actions = [ActionType.READ] * 7 + [ActionType.VIEW_PROFILE] * 3
        elif stage < 50:
            actions = (
                [ActionType.READ] * 4
                + [ActionType.REACT] * 3
                + [ActionType.VIEW_PROFILE] * 2
                + [ActionType.SUBSCRIBE] * 1
            )
        else:
            actions = (
                [ActionType.READ] * 3
                + [ActionType.REACT] * 3
                + [ActionType.SUBSCRIBE] * 2
                + [ActionType.VIEW_PROFILE] * 1
                + [ActionType.COMMENT] * 1
            )
        return random.choice(actions)

    @staticmethod
    async def start_warming(db: AsyncSession, account_ids: list[str]):
        """Mark accounts for warming."""
        for account_id in account_ids:
            account = await db.get(Account, account_id)
            if account and account.status == AccountStatus.ACTIVE:
                account.status = AccountStatus.WARMING
                account.warming_stage = 0
        await db.commit()
        logger.info("Accounts marked for warming", count=len(account_ids))


warming_service = WarmingService()
