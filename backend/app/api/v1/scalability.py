from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.pipeline_agent import pipeline_agent
from app.services.anomaly_detector import anomaly_detector
from app.services.channel_scorer import channel_scorer
from app.services.smart_scheduler import smart_scheduler
from app.services.ab_tester import ab_tester
from app.services.task_queue import task_queue

router = APIRouter(prefix="/scalability", tags=["scalability"])


# ─── PIPELINE AGENT ─────────────────────────────────────────


@router.post("/pipeline/start")
async def start_pipeline():
    """Start the full autonomous pipeline."""
    await pipeline_agent.start()
    return {"started": True}


@router.post("/pipeline/stop")
async def stop_pipeline():
    """Stop the pipeline agent."""
    await pipeline_agent.stop()
    return {"stopped": True}


@router.get("/pipeline/status")
async def pipeline_status():
    """Get pipeline agent status."""
    return pipeline_agent.get_status()


# ─── ANOMALY DETECTOR ───────────────────────────────────────


@router.post("/anomaly/start")
async def start_anomaly_detection():
    """Start anomaly detection."""
    await anomaly_detector.start()
    return {"started": True}


@router.post("/anomaly/stop")
async def stop_anomaly_detection():
    """Stop anomaly detection."""
    await anomaly_detector.stop()
    return {"stopped": True}


@router.get("/anomaly/history")
async def anomaly_history():
    """Get anomaly detection history."""
    return anomaly_detector.get_history()


# ─── CHANNEL SCORER ─────────────────────────────────────────


@router.post("/channels/score")
async def score_channels():
    """Recalculate channel scores."""
    await channel_scorer.score_all_channels()
    return {"scored": True}


@router.get("/channels/best")
async def best_channels(limit: int = 10):
    """Get highest-scored channels."""
    channels = await channel_scorer.get_best_channels(limit)
    return [
        {
            "id": c.id,
            "name": c.name,
            "score": c.quality_score,
            "subscribers": c.subscribers,
        }
        for c in channels
    ]


@router.get("/channels/worst")
async def worst_channels(limit: int = 10):
    """Get lowest-scored channels."""
    channels = await channel_scorer.get_worst_channels(limit)
    return [
        {
            "id": c.id,
            "name": c.name,
            "score": c.quality_score,
            "subscribers": c.subscribers,
        }
        for c in channels
    ]


# ─── SMART SCHEDULER ────────────────────────────────────────


@router.get("/scheduler/available")
async def available_accounts(limit: int = 10):
    """Get accounts available now (timezone-aware)."""
    accounts = await smart_scheduler.get_next_available_accounts(limit)
    return [
        {"id": a.id, "phone": a.phone, "geo": a.geo, "stage": a.warming_stage}
        for a in accounts
    ]


# ─── A/B TESTING ────────────────────────────────────────────


@router.get("/abtest/leaderboard")
async def ab_leaderboard():
    """Get prompt variant performance ranking."""
    return await ab_tester.get_leaderboard()


@router.post("/abtest/select")
async def select_variant(role: str = "commenting"):
    """Select a prompt variant for testing."""
    return await ab_tester.select_variant(role)


# ─── TASK QUEUE ──────────────────────────────────────────────


@router.get("/queue/stats")
async def queue_stats():
    """Get task queue statistics."""
    return await task_queue.get_stats()
