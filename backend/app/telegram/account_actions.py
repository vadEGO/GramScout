import asyncio
import random
from datetime import datetime
from typing import Optional
from telethon import TelegramClient
from telethon.errors import FloodWaitError, ChatWriteForbiddenError, ChannelPrivateError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.logging import logger
from app.models.account import Account, AccountStatus
from app.models.action_log import ActionLog, ActionType, ActionResult
from app.telegram.client_manager import client_manager


class AccountActions:
    """High-level Telegram actions for accounts."""

    @staticmethod
    async def subscribe_to_channel(
        db: AsyncSession, account: Account, channel_username: str
    ) -> bool:
        """Subscribe account to a channel."""
        client = await client_manager.get_client(account)
        if not client:
            return False

        try:
            await client(functions.channels.JoinChannelRequest(channel_username))
            log = ActionLog(
                account_id=account.id,
                action_type=ActionType.SUBSCRIBE,
                target_channel=channel_username,
                result=ActionResult.SUCCESS,
            )
            db.add(log)
            await db.commit()
            logger.info("Subscribed", account_id=account.id, channel=channel_username)
            return True

        except FloodWaitError as e:
            await client_manager.handle_flood_wait(account.id, e.seconds)
            log = ActionLog(
                account_id=account.id,
                action_type=ActionType.SUBSCRIBE,
                target_channel=channel_username,
                result=ActionResult.FAILED,
                error_message=f"FloodWait: {e.seconds}s",
            )
            db.add(log)
            await db.commit()
            return False

        except (ChatWriteForbiddenError, ChannelPrivateError) as e:
            log = ActionLog(
                account_id=account.id,
                action_type=ActionType.SUBSCRIBE,
                target_channel=channel_username,
                result=ActionResult.FAILED,
                error_message=str(e),
            )
            db.add(log)
            await db.commit()
            return False

        except Exception as e:
            logger.error("Subscribe failed", account_id=account.id, error=str(e))
            return False

    @staticmethod
    async def post_comment(
        db: AsyncSession,
        account: Account,
        channel_username: str,
        post_id: int,
        comment_text: str,
    ) -> bool:
        """Post a comment on a channel post."""
        client = await client_manager.get_client(account)
        if not client:
            return False

        try:
            await asyncio.sleep(random.uniform(1.0, 3.0))

            entity = await client.get_entity(channel_username)
            await client.send_message(entity, comment_text, comment_to=post_id)

            log = ActionLog(
                account_id=account.id,
                action_type=ActionType.COMMENT,
                target_channel=channel_username,
                target_post_id=str(post_id),
                content=comment_text[:200],
                result=ActionResult.SUCCESS,
            )
            db.add(log)
            await db.commit()

            logger.info(
                "Comment posted",
                account_id=account.id,
                channel=channel_username,
                post_id=post_id,
            )
            return True

        except FloodWaitError as e:
            await client_manager.handle_flood_wait(account.id, e.seconds)
            log = ActionLog(
                account_id=account.id,
                action_type=ActionType.COMMENT,
                target_channel=channel_username,
                result=ActionResult.FAILED,
                error_message=f"FloodWait: {e.seconds}s",
            )
            db.add(log)
            await db.commit()
            return False

        except Exception as e:
            logger.error("Comment failed", account_id=account.id, error=str(e))
            return False

    @staticmethod
    async def add_reaction(
        db: AsyncSession,
        account: Account,
        channel_username: str,
        post_id: int,
        emoji: str = "👍",
    ) -> bool:
        """Add a reaction to a post."""
        client = await client_manager.get_client(account)
        if not client:
            return False

        try:
            entity = await client.get_entity(channel_username)
            await client(
                functions.messages.SendReactionRequest(
                    peer=entity,
                    msg_id=post_id,
                    reaction=[types.ReactionEmoji(emoticon=emoji)],
                )
            )

            log = ActionLog(
                account_id=account.id,
                action_type=ActionType.REACT,
                target_channel=channel_username,
                target_post_id=str(post_id),
                content=emoji,
                result=ActionResult.SUCCESS,
            )
            db.add(log)
            await db.commit()
            return True

        except FloodWaitError as e:
            await client_manager.handle_flood_wait(account.id, e.seconds)
            return False

        except Exception as e:
            logger.error("Reaction failed", account_id=account.id, error=str(e))
            return False


# Import telethon functions at module level
from telethon.tl import functions, types
