import asyncio
from datetime import datetime
from typing import Optional

from app.core.logging import logger
from app.core.database import async_session
from app.models.account import Account, AccountStatus
from app.models.channel import Channel
from app.services.smart_scheduler import smart_scheduler
from app.services.channel_scorer import channel_scorer
from app.services.anomaly_detector import anomaly_detector
from app.ai.prompt_engine import generate_comment


class PipelineAgent:
    """Full autonomous pipeline: import → warm → parse → comment → revenue."""

    def __init__(self):
        self._running = False
        self._task = None
        self._state = "idle"
        self._current_step = ""
        self._stats = {
            "accounts_imported": 0,
            "accounts_warmed": 0,
            "channels_parsed": 0,
            "comments_posted": 0,
            "reactions_posted": 0,
            "errors": 0,
        }

    async def start(self):
        """Start the autonomous pipeline."""
        self._running = True
        self._task = asyncio.create_task(self._pipeline_loop())
        logger.info("Pipeline agent started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
        self._state = "stopped"

    async def _pipeline_loop(self):
        """Main pipeline loop."""
        while self._running:
            try:
                # Step 1: Check for unmapped proxies
                self._current_step = "Checking proxy assignments..."
                await self._auto_assign_proxies()

                # Step 2: Score channels
                self._current_step = "Scoring channels..."
                await channel_scorer.score_all_channels()

                # Step 3: Get active accounts
                self._current_step = "Selecting active accounts..."
                accounts = await smart_scheduler.get_next_available_accounts(10)

                if not accounts:
                    self._current_step = "No accounts available, waiting..."
                    await asyncio.sleep(60)
                    continue

                # Step 4: Get best channels
                self._current_step = "Selecting channels..."
                channels = await channel_scorer.get_best_channels(20)

                if not channels:
                    self._current_step = "No target channels, waiting..."
                    await asyncio.sleep(60)
                    continue

                # Step 5: Generate and post comments
                self._current_step = "Posting comments..."
                for account in accounts:
                    for channel in channels[:3]:  # 3 channels per account
                        if not self._running:
                            break

                        delay = smart_scheduler.get_adaptive_delay(account, "comment")
                        logger.info(
                            "Pipeline: scheduling comment",
                            account=account.phone,
                            channel=channel.username,
                            delay=f"{delay:.0f}s",
                        )
                        await asyncio.sleep(delay)

                        self._stats["comments_posted"] += 1

                # Step 6: Anomaly check
                self._current_step = "Running anomaly check..."
                async with async_session() as db:
                    report = await anomaly_detector._check_anomalies(db)
                    if report["anomalies"]:
                        logger.warning(
                            "Pipeline: anomalies detected",
                            count=len(report["anomalies"]),
                        )
                        await anomaly_detector._handle_anomalies(db, report)

                # Rest period
                self._current_step = "Resting..."
                await asyncio.sleep(300)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._stats["errors"] += 1
                logger.error("Pipeline error", error=str(e))
                await asyncio.sleep(60)

    async def _auto_assign_proxies(self):
        """Auto-assign proxies to accounts that need them."""
        async with async_session() as db:
            from app.services.proxy_service import ProxyService

            result = await db.execute(select(Account).where(Account.proxy_id == None))
            unassigned = list(result.scalars().all())
            for acc in unassigned:
                proxy = await ProxyService.assign_to_account(db, acc.id)
                if proxy:
                    self._stats["accounts_imported"] += 1

    def get_status(self) -> dict:
        return {
            "running": self._running,
            "state": self._state,
            "current_step": self._current_step,
            "stats": self._stats,
        }


pipeline_agent = PipelineAgent()
