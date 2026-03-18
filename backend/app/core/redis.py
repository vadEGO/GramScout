import redis.asyncio as redis
from app.config import settings

pool = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)
redis_client = redis.Redis(connection_pool=pool)


async def get_redis() -> redis.Redis:
    return redis_client
