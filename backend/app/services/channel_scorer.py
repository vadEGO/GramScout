import asyncio
import random
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.core.database import async_session
from app.models.channel import Channel
from app.models.action_log import ActionLog, ActionType, ActionResult


class ChannelScorer:
    """Scores channels based on success rate and engagement."""

    async def score_all_channels(self):
        """Recalculate scores for all channels."""
        async with async_session() as db:
            result = await db.execute(select(Channel))
            channels = list(result.scalars().all())

            for ch in channels:
                score = await self._calculate_score(db, ch)
                ch.quality_score = score

            await db.commit()
            logger.info("Channel scores updated", count=len(channels))

    async def _calculate_score(self, db: AsyncSession, channel: Channel) -> float:
        """Calculate channel quality score (0-10)."""
        score = 5.0  # Base score

        # Success rate bonus
        successes = (
            await db.execute(
                select(func.count(ActionLog.id)).where(
                    ActionLog.target_channel == channel.url,
                    ActionLog.result == ActionResult.SUCCESS,
                )
            )
        ).scalar() or 0

        failures = (
            await db.execute(
                select(func.count(ActionLog.id)).where(
                    ActionLog.target_channel == channel.url,
                    ActionLog.result.in_([ActionResult.BANNED, ActionResult.MUTED]),
                )
            )
        ).scalar() or 0

        total = successes + failures
        if total > 0:
            success_rate = successes / total
            score += success_rate * 3  # Up to +3 for 100% success

        # Subscriber count bonus
        if channel.subscribers > 100000:
            score += 1
        elif channel.subscribers > 10000:
            score += 0.5

        # Open comments bonus
        if channel.open_comments:
            score += 1

        # Penalties
        if failures > 10:
            score -= 2
        elif failures > 5:
            score -= 1

        return max(0, min(10, round(score, 1)))

    async def get_best_channels(self, limit: int = 10) -> list[Channel]:
        """Get highest-scored channels."""
        async with async_session() as db:
            result = await db.execute(
                select(Channel)
                .where(Channel.is_target == True, Channel.open_comments == True)
                .order_by(Channel.quality_score.desc())
                .limit(limit)
            )
            return list(result.scalars().all())

    async def get_worst_channels(self, limit: int = 10) -> list[Channel]:
        """Get lowest-scored channels (candidates for blacklist)."""
        async with async_session() as db:
            result = await db.execute(
                select(Channel)
                .where(Channel.is_target == True)
                .order_by(Channel.quality_score.asc())
                .limit(limit)
            )
            return list(result.scalars().all())


channel_scorer = ChannelScorer()
