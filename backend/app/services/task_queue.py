import asyncio
import json
import time
from typing import Any, Callable, Optional
from datetime import datetime

from app.core.redis import redis_client
from app.core.logging import logger


class TaskQueue:
    """Redis-based task queue for scalable parallel processing."""

    def __init__(self):
        self._running = False
        self._workers: list[asyncio.Task] = []
        self._handlers: dict[str, Callable] = {}

    def register_handler(self, task_type: str, handler: Callable):
        """Register a handler for a task type."""
        self._handlers[task_type] = handler

    async def enqueue(self, task_type: str, payload: dict, priority: int = 5):
        """Add a task to the queue."""
        task = {
            "id": str(uuid.uuid4()),
            "type": task_type,
            "payload": payload,
            "priority": priority,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "retry_count": 0,
            "max_retries": 3,
        }
        await redis_client.lpush(f"queue:{task_type}", json.dumps(task))
        await redis_client.incr("queue:stats:enqueued")
        logger.info("Task enqueued", type=task_type, priority=priority)
        return task["id"]

    async def dequeue(self, task_type: str, timeout: int = 5) -> Optional[dict]:
        """Get next task from queue."""
        result = await redis_client.brpop(f"queue:{task_type}", timeout=timeout)
        if result:
            _, task_json = result
            return json.loads(task_json)
        return None

    async def start_workers(self, task_type: str, num_workers: int = 3):
        """Start worker tasks for a task type."""
        handler = self._handlers.get(task_type)
        if not handler:
            raise ValueError(f"No handler registered for {task_type}")

        for i in range(num_workers):
            task = asyncio.create_task(
                self._worker_loop(task_type, handler, f"{task_type}-{i}")
            )
            self._workers.append(task)
        logger.info(f"Started {num_workers} workers for {task_type}")

    async def _worker_loop(self, task_type: str, handler: Callable, worker_id: str):
        """Worker loop that processes tasks."""
        while self._running:
            try:
                task = await self.dequeue(task_type, timeout=5)
                if task:
                    logger.info(
                        "Processing task",
                        worker=worker_id,
                        type=task_type,
                        id=task["id"],
                    )
                    try:
                        await handler(task["payload"])
                        await redis_client.incr("queue:stats:completed")
                    except Exception as e:
                        task["retry_count"] += 1
                        if task["retry_count"] < task["max_retries"]:
                            await asyncio.sleep(5 * task["retry_count"])
                            await redis_client.lpush(
                                f"queue:{task_type}", json.dumps(task)
                            )
                        else:
                            await redis_client.incr("queue:stats:failed")
                            logger.error(
                                "Task failed permanently", id=task["id"], error=str(e)
                            )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Worker error", worker=worker_id, error=str(e))
                await asyncio.sleep(1)

    async def stop(self):
        """Stop all workers."""
        self._running = False
        for w in self._workers:
            w.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

    async def get_stats(self) -> dict:
        """Get queue statistics."""
        enqueued = await redis_client.get("queue:stats:enqueued")
        completed = await redis_client.get("queue:stats:completed")
        failed = await redis_client.get("queue:stats:failed")
        return {
            "enqueued": int(enqueued or 0),
            "completed": int(completed or 0),
            "failed": int(failed or 0),
            "active_workers": len(self._workers),
        }


import uuid

task_queue = TaskQueue()
