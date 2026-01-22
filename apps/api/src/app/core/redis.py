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


async def get_redis() -> Redis | None:
    """
    Get Redis client instance.

    Returns None if Redis is not available (optional dependency).

    Usage in FastAPI:
        @app.get("/cached")
        async def get_cached(redis: Redis | None = Depends(get_redis)):
            if redis is None:
                # Handle case where Redis is unavailable
                ...
    """
    return redis_client


def is_redis_available() -> bool:
    """Check if Redis client is initialized and available."""
    return redis_client is not None


async def close_redis() -> None:
    """Close Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
