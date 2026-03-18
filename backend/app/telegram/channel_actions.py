import asyncio
import random
from datetime import datetime
from typing import Optional
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.functions.channels import GetFullChannelRequest

from app.core.logging import logger
from app.models.account import Account
from app.models.channel import Channel
from app.telegram.client_manager import client_manager


class ChannelActions:
    """Channel-specific Telegram actions."""

    @staticmethod
    async def get_channel_info(client, channel_username: str) -> Optional[dict]:
        """Get channel information."""
        try:
            entity = await client.get_entity(channel_username)
            full = await client(GetFullChannelRequest(entity))

            return {
                "id": entity.id,
                "title": entity.title,
                "username": getattr(entity, "username", None),
                "participants_count": full.full_chat.participants_count,
                "about": full.full_chat.about,
                "is_megagroup": getattr(entity, "megagroup", False),
            }
        except Exception as e:
            logger.error(
                "Failed to get channel info", channel=channel_username, error=str(e)
            )
            return None

    @staticmethod
    async def get_recent_posts(
        client, channel_username: str, limit: int = 50
    ) -> list[dict]:
        """Get recent posts from a channel."""
        try:
            entity = await client.get_entity(channel_username)
            history = await client(
                GetHistoryRequest(
                    peer=entity,
                    limit=limit,
                    offset_date=None,
                    offset_id=0,
                    max_id=0,
                    min_id=0,
                    add_offset=0,
                    hash=0,
                )
            )

            posts = []
            for msg in history.messages:
                if msg.message:
                    posts.append(
                        {
                            "id": msg.id,
                            "text": msg.message,
                            "date": msg.date.isoformat() if msg.date else None,
                            "views": getattr(msg, "views", 0),
                            "forwards": getattr(msg, "forwards", 0),
                        }
                    )
            return posts

        except Exception as e:
            logger.error("Failed to get posts", channel=channel_username, error=str(e))
            return []

    @staticmethod
    async def search_channels(
        client,
        query: str,
        limit: int = 20,
    ) -> list[dict]:
        """Search for channels by query."""
        try:
            from telethon.tl.functions.contacts import SearchRequest

            result = await client(SearchRequest(q=query, limit=limit))

            channels = []
            for chat in result.chats:
                if hasattr(chat, "username") and chat.username:
                    channels.append(
                        {
                            "id": chat.id,
                            "title": chat.title,
                            "username": chat.username,
                            "participants_count": getattr(
                                chat, "participants_count", 0
                            ),
                        }
                    )
            return channels

        except Exception as e:
            logger.error("Channel search failed", query=query, error=str(e))
            return []
