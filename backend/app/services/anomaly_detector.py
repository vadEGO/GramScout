import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.core.database import async_session
from app.models.account import Account, AccountStatus
from app.models.action_log import ActionLog, ActionType, ActionResult


class AnomalyDetector:
    """Detects anomalies and takes corrective action."""

    def __init__(self):
        self._running = False
        self._task = None
        self._check_interval = 300  # 5 minutes
        self._ban_rate_threshold = 0.10  # 10%
        self._flood_rate_threshold = 0.25  # 25%
        self._history = []

    async def start(self):
        """Start the anomaly detection loop."""
        self._running = True
        self._task = asyncio.create_task(self._detection_loop())
        logger.info("Anomaly detector started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()

    async def _detection_loop(self):
        while self._running:
            try:
                async with async_session() as db:
                    report = await self._check_anomalies(db)
                    if report["anomalies"]:
                        await self._handle_anomalies(db, report)
                    self._history.append(
                        {
                            "timestamp": datetime.utcnow().isoformat(),
                            **report,
                        }
                    )
                    if len(self._history) > 100:
                        self._history = self._history[-100:]
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Anomaly detection error", error=str(e))
            await asyncio.sleep(self._check_interval)

    async def _check_anomalies(self, db: AsyncSession) -> dict:
        """Check for anomalies across all metrics."""
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)

        anomalies = []

        # Check ban rate (last hour)
        recent_bans = (
            await db.execute(
                select(func.count(ActionLog.id)).where(
                    ActionLog.result == ActionResult.BANNED,
                    ActionLog.timestamp >= hour_ago,
                )
            )
        ).scalar() or 0

        recent_actions = (
            await db.execute(
                select(func.count(ActionLog.id)).where(ActionLog.timestamp >= hour_ago)
            )
        ).scalar() or 1

        ban_rate = recent_bans / recent_actions

        if ban_rate > self._ban_rate_threshold:
            anomalies.append(
                {
                    "type": "high_ban_rate",
                    "severity": "critical",
                    "value": round(ban_rate, 3),
                    "threshold": self._ban_rate_threshold,
                    "message": f"Ban rate {ban_rate:.1%} exceeds threshold {self._ban_rate_threshold:.0%}",
                }
            )

        # Check flood wait rate
        flood_waits = (
            await db.execute(
                select(func.count(ActionLog.id)).where(
                    ActionLog.result == ActionResult.FAILED,
                    ActionLog.error_message.like("%FloodWait%"),
                    ActionLog.timestamp >= hour_ago,
                )
            )
        ).scalar() or 0

        flood_rate = flood_waits / max(recent_actions, 1)

        if flood_rate > self._flood_rate_threshold:
            anomalies.append(
                {
                    "type": "high_flood_rate",
                    "severity": "warning",
                    "value": round(flood_rate, 3),
                    "message": f"Flood wait rate {flood_rate:.1%} is high",
                }
            )

        # Check for mass bans (multiple bans in short time)
        if recent_bans > 5:
            anomalies.append(
                {
                    "type": "mass_bans",
                    "severity": "critical",
                    "value": recent_bans,
                    "message": f"{recent_bans} bans in the last hour",
                }
            )

        # Check for sudden drop in active accounts
        active_count = (
            await db.execute(
                select(func.count(Account.id)).where(
                    Account.status.in_([AccountStatus.ACTIVE, AccountStatus.WORKING])
                )
            )
        ).scalar() or 0

        total_count = (await db.execute(select(func.count(Account.id)))).scalar() or 1

        if active_count / total_count < 0.5 and total_count > 5:
            anomalies.append(
                {
                    "type": "low_active_ratio",
                    "severity": "warning",
                    "value": active_count / total_count,
                    "message": f"Only {active_count}/{total_count} accounts active",
                }
            )

        return {
            "anomalies": anomalies,
            "metrics": {
                "ban_rate": round(ban_rate, 4),
                "flood_rate": round(flood_rate, 4),
                "recent_bans": recent_bans,
                "recent_actions": recent_actions,
                "active_accounts": active_count,
                "total_accounts": total_count,
            },
        }

    async def _handle_anomalies(self, db: AsyncSession, report: dict):
        """Take corrective action based on anomalies."""
        for anomaly in report["anomalies"]:
            if anomaly["type"] == "high_ban_rate" and anomaly["severity"] == "critical":
                # Pause all commenting
                result = await db.execute(
                    select(Account).where(Account.status == AccountStatus.WORKING)
                )
                working = list(result.scalars().all())
                for acc in working:
                    acc.status = AccountStatus.ACTIVE
                await db.commit()
                logger.warning(
                    "AUTO-PAUSE: High ban rate detected", paused_accounts=len(working)
                )

            elif anomaly["type"] == "mass_bans":
                # Quarantine recently active accounts
                cutoff = datetime.utcnow() - timedelta(hours=2)
                result = await db.execute(
                    select(Account).where(
                        Account.status.in_(
                            [AccountStatus.ACTIVE, AccountStatus.WORKING]
                        ),
                        Account.last_active >= cutoff,
                    )
                )
                recent = list(result.scalars().all())
                for acc in recent:
                    acc.status = AccountStatus.MUTED
                await db.commit()
                logger.warning(
                    "AUTO-QUARANTINE: Mass bans detected", quarantined=len(recent)
                )

    def get_history(self) -> list:
        return self._history


anomaly_detector = AnomalyDetector()
