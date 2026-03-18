import asyncio
import random
from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.core.database import async_session
from app.models.account import Account, AccountStatus


class SmartScheduler:
    """Timezone-aware scheduling with adaptive delays."""

    # Peak hours per timezone offset (UTC offset -> peak hours)
    PEAK_HOURS = {
        "americas": [(9, 12), (18, 22)],
        "europe": [(8, 11), (17, 21)],
        "asia": [(7, 10), (19, 23)],
    }

    def get_timezone_region(self, country_code: str) -> str:
        """Map country code to timezone region."""
        americas = ["US", "CA", "BR", "MX", "AR", "CO"]
        europe = ["UK", "DE", "FR", "IT", "ES", "NL", "UA", "RU", "PL"]
        asia = ["JP", "KR", "CN", "IN", "AU", "SG"]

        cc = country_code.upper()
        if cc in americas:
            return "americas"
        elif cc in europe:
            return "europe"
        elif cc in asia:
            return "asia"
        return "europe"  # default

    def is_peak_hour(self, account: Account) -> bool:
        """Check if current time is peak hour for this account's region."""
        region = self.get_timezone_region(account.geo)
        now = datetime.utcnow()
        current_hour = now.hour

        for start, end in self.PEAK_HOURS.get(region, []):
            if start <= current_hour < end:
                return True
        return False

    def is_sleep_hour(self, account: Account) -> bool:
        """Check if account should be sleeping based on its timezone."""
        region = self.get_timezone_region(account.geo)
        now = datetime.utcnow()
        current_hour = now.hour

        # Sleep hours: 1am-7am local time
        sleep_ranges = {
            "americas": (5, 13),  # UTC hours for Americas night
            "europe": (1, 7),  # UTC hours for Europe night
            "asia": (17, 23),  # UTC hours for Asia night
        }
        start, end = sleep_ranges.get(region, (2, 8))
        return start <= current_hour < end

    def get_adaptive_delay(self, account: Account, action_type: str) -> float:
        """Get adaptive delay based on time, trust score, and action type."""
        base_delays = {
            "comment": (60, 300),
            "react": (10, 60),
            "read": (5, 30),
            "subscribe": (120, 600),
        }

        min_d, max_d = base_delays.get(action_type, (30, 120))

        # Longer delays at peak hours (more scrutiny)
        if self.is_peak_hour(account):
            min_d = int(min_d * 1.5)
            max_d = int(max_d * 1.5)

        # Shorter delays if account has high trust
        if account.warming_stage > 80:
            min_d = int(min_d * 0.8)
            max_d = int(max_d * 0.8)

        # Much longer delays if account is new
        if account.warming_stage < 20:
            min_d = int(min_d * 2)
            max_d = int(max_d * 2)

        return random.uniform(min_d, max_d)

    def get_jitter(self, base_delay: float) -> float:
        """Add human-like jitter to delays."""
        jitter = base_delay * random.uniform(-0.3, 0.3)
        return base_delay + jitter

    async def should_account_be_active(self, account: Account) -> bool:
        """Check if account should be active now."""
        if self.is_sleep_hour(account):
            return False
        if account.status not in [AccountStatus.ACTIVE, AccountStatus.WORKING]:
            return False
        return True

    async def get_next_available_accounts(self, limit: int = 10) -> list[Account]:
        """Get accounts that should be active now."""
        async with async_session() as db:
            result = await db.execute(
                select(Account).where(
                    Account.status.in_([AccountStatus.ACTIVE, AccountStatus.WORKING])
                )
            )
            all_accounts = list(result.scalars().all())

            available = [
                a for a in all_accounts if await self.should_account_be_active(a)
            ]
            random.shuffle(available)
            return available[:limit]


smart_scheduler = SmartScheduler()
