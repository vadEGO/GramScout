import asyncio
import random
from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.logging import logger
from app.models.account import Account, AccountStatus
from app.models.action_log import ActionLog, ActionType, ActionResult
from app.models.channel import Channel
from app.ai.prompt_engine import generate_comment
from app.telegram.account_actions import AccountActions


class CommentService:
    """Neurocommenting engine - generates and posts AI comments."""

    def __init__(self):
        self._running = False
        self._workers: list[asyncio.Task] = []
        self._comment_queue: asyncio.Queue = asyncio.Queue()

    async def start(self, db: AsyncSession, num_workers: int = 5):
        """Start comment workers."""
        self._running = True
        for i in range(num_workers):
            task = asyncio.create_task(self._worker(db, f"worker-{i}"))
            self._workers.append(task)
        logger.info("Comment engine started", workers=num_workers)

    async def stop(self):
        """Stop all comment workers."""
        self._running = False
        for task in self._workers:
            task.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        logger.info("Comment engine stopped")

    async def _worker(self, db: AsyncSession, worker_id: str):
        """Individual comment worker."""
        while self._running:
            try:
                job = await asyncio.wait_for(self._comment_queue.get(), timeout=5.0)
                await self._process_job(db, job, worker_id)
                self._comment_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Worker error", worker=worker_id, error=str(e))
                await asyncio.sleep(5)

    async def _process_job(self, db: AsyncSession, job: dict, worker_id: str):
        """Process a single comment job."""
        account_id = job["account_id"]
        channel_username = job["channel_username"]
        post_id = job["post_id"]
        post_text = job["post_text"]
        persona = job.get("persona", {})

        account = await db.get(Account, account_id)
        if not account or account.status not in (
            AccountStatus.ACTIVE,
            AccountStatus.WORKING,
        ):
            return

        delay = random.uniform(
            settings.DEFAULT_COMMENT_DELAY_MIN,
            settings.DEFAULT_COMMENT_DELAY_MAX,
        )
        logger.info(
            "Processing comment job",
            worker=worker_id,
            account=account_id,
            channel=channel_username,
            delay=f"{delay:.0f}s",
        )

        await asyncio.sleep(delay)

        comment_text = await generate_comment(
            post_text=post_text,
            persona=persona or account.persona or {},
            channel_context=channel_username,
        )

        if not comment_text:
            logger.warning("Failed to generate comment", account=account_id)
            return

        success = await AccountActions.post_comment(
            db=db,
            account=account,
            channel_username=channel_username,
            post_id=post_id,
            comment_text=comment_text,
        )

        if success:
            account.last_active = datetime.utcnow()
            await db.commit()
            logger.info("Comment posted", worker=worker_id, account=account_id)

    async def enqueue_comment(
        self,
        account_id: str,
        channel_username: str,
        post_id: int,
        post_text: str,
        persona: Optional[dict] = None,
    ):
        """Add a comment job to the queue."""
        await self._comment_queue.put(
            {
                "account_id": account_id,
                "channel_username": channel_username,
                "post_id": post_id,
                "post_text": post_text,
                "persona": persona,
            }
        )

    async def queue_size(self) -> int:
        return self._comment_queue.qsize()


comment_service = CommentService()
