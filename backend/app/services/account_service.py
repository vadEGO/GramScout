import uuid
import asyncio
from datetime import datetime
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.logging import logger
from app.core.security import encrypt
from app.models.account import Account, AccountStatus, AccountFormat
from app.ai.prompt_engine import generate_persona
from app.ai.llm_client import DEFAULT_MODELS


class AccountService:
    """Account management service."""

    @staticmethod
    async def create(
        db: AsyncSession,
        phone: str,
        country_code: str,
        format: AccountFormat = AccountFormat.TDATA,
        session_string: Optional[str] = None,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> Account:
        """Create a new account with generated persona."""
        persona = generate_persona()
        model = DEFAULT_MODELS["primary"]
        gender = persona.get("gender", "unspecified")

        account = Account(
            id=str(uuid.uuid4()),
            phone=phone,
            country_code=country_code,
            geo=country_code.replace("+", ""),
            format=format,
            status=AccountStatus.ACTIVE,
            session_string=encrypt(session_string) if session_string else None,
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            persona=persona,
            assigned_model=model,
            gender=gender,
        )

        db.add(account)
        await db.commit()
        await db.refresh(account)

        logger.info(
            "Account created",
            account_id=account.id,
            phone=phone,
            persona=persona["personality_type"],
        )
        return account

    @staticmethod
    async def get(db: AsyncSession, account_id: str) -> Optional[Account]:
        result = await db.execute(select(Account).where(Account.id == account_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        db: AsyncSession,
        status: Optional[AccountStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Account]:
        query = select(Account).offset(offset).limit(limit)
        if status:
            query = query.where(Account.status == status)
        result = await db.execute(query.order_by(Account.created_at.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def update_status(
        db: AsyncSession, account_id: str, status: AccountStatus
    ) -> Optional[Account]:
        account = await AccountService.get(db, account_id)
        if account:
            account.status = status
            account.last_active = datetime.utcnow()
            await db.commit()
            await db.refresh(account)
        return account

    @staticmethod
    async def get_active_accounts(db: AsyncSession) -> list[Account]:
        result = await db.execute(
            select(Account).where(
                Account.status.in_([AccountStatus.ACTIVE, AccountStatus.WORKING])
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_available_for_commenting(db: AsyncSession) -> list[Account]:
        """Get accounts available for commenting (not banned, muted, or in flood wait)."""
        result = await db.execute(
            select(Account).where(
                Account.status.in_([AccountStatus.ACTIVE, AccountStatus.WORKING]),
                Account.warming_stage >= 30,
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def count_by_status(db: AsyncSession) -> dict:
        result = await db.execute(
            select(Account.status, func.count(Account.id)).group_by(Account.status)
        )
        return {row[0].value: row[1] for row in result.all()}

    @staticmethod
    async def delete(db: AsyncSession, account_id: str) -> bool:
        account = await AccountService.get(db, account_id)
        if account:
            await db.delete(account)
            await db.commit()
            return True
        return False
