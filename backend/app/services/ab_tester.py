import asyncio
import random
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.core.database import async_session
from app.models import PromptTemplate


class ABTester:
    """A/B testing for prompt templates to optimize conversion."""

    def __init__(self):
        self._metrics: dict[str, dict] = {}

    async def select_variant(self, role: str = "commenting") -> dict:
        """Select a prompt variant using epsilon-greedy strategy."""
        async with async_session() as db:
            result = await db.execute(
                select(PromptTemplate).where(
                    PromptTemplate.is_active == True,
                    PromptTemplate.use_case == role,
                )
            )
            variants = list(result.scalars().all())

            if not variants:
                return self._default_prompt()

            # Epsilon-greedy: 20% explore, 80% exploit
            if random.random() < 0.2:
                chosen = random.choice(variants)
            else:
                chosen = max(variants, key=lambda v: self._get_success_rate(v.id))

            return {
                "id": chosen.id,
                "name": chosen.name,
                "system_prompt": chosen.system_prompt,
                "temperature": chosen.temperature,
                "max_tokens": chosen.max_tokens,
            }

    def _default_prompt(self) -> dict:
        return {
            "id": "default",
            "name": "Default",
            "system_prompt": "You are a real person commenting on Telegram. Write like texting a friend. Be opinionated. 15-40 words.",
            "temperature": 0.75,
            "max_tokens": 60,
        }

    def _get_success_rate(self, variant_id: str) -> float:
        """Get success rate for a variant."""
        metrics = self._metrics.get(variant_id, {"attempts": 0, "successes": 0})
        if metrics["attempts"] == 0:
            return 0.5  # Default for untested variants
        return metrics["successes"] / metrics["attempts"]

    def record_result(self, variant_id: str, success: bool):
        """Record the result of using a variant."""
        if variant_id not in self._metrics:
            self._metrics[variant_id] = {"attempts": 0, "successes": 0}
        self._metrics[variant_id]["attempts"] += 1
        if success:
            self._metrics[variant_id]["successes"] += 1

    async def get_leaderboard(self) -> list[dict]:
        """Get performance ranking of all variants."""
        async with async_session() as db:
            result = await db.execute(
                select(PromptTemplate).where(PromptTemplate.is_active == True)
            )
            variants = list(result.scalars().all())

            leaderboard = []
            for v in variants:
                metrics = self._metrics.get(v.id, {"attempts": 0, "successes": 0})
                rate = (
                    (metrics["successes"] / metrics["attempts"] * 100)
                    if metrics["attempts"] > 0
                    else 0
                )
                leaderboard.append(
                    {
                        "name": v.name,
                        "attempts": metrics["attempts"],
                        "success_rate": round(rate, 1),
                        "temperature": v.temperature,
                    }
                )

            return sorted(leaderboard, key=lambda x: x["success_rate"], reverse=True)


ab_tester = ABTester()
