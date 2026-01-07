"""
Redis Configuration

Async Redis client for sessions and caching.
"""

from redis.asyncio import Redis, from_url

from app.core.config import settings

# Redis client instance
redis_client: Redis | None = None


async def init_redis() -> Redis:
    """
    Initialize Redis connection.

    Call this on application startup.
    """
    global redis_client
    redis_client = from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )
    # Test connection
    await redis_client.ping()
    return redis_client


async def get_redis() -> Redis:
    """
    Get Redis client instance.

    Usage in FastAPI:
        @app.get("/cached")
        async def get_cached(redis: Redis = Depends(get_redis)):
            ...
    """
    if redis_client is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
