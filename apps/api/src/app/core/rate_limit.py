"""
Rate Limiting Module

Provides rate limiting for API endpoints using Redis as the backend.
Falls back to in-memory storage if Redis is unavailable.

SECURITY: Rate limiting prevents abuse of sensitive endpoints like:
- Admin approval/rejection (prevents mass operations)
- Authentication endpoints (prevents brute force)
- Email-sending endpoints (prevents spam)
"""

import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

from fastapi import HTTPException, Request, status

from app.core.config import settings

logger = logging.getLogger(__name__)

# In-memory rate limit storage (fallback when Redis unavailable)
# Format: {key: [(timestamp, count), ...]}
_memory_store: dict[str, list[tuple[float, int]]] = {}


class RateLimitExceeded(HTTPException):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, limit: int, window_seconds: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "RATE_LIMIT_EXCEEDED",
                "message": f"Rate limit exceeded. Maximum {limit} requests per {window_seconds} seconds.",
                "retry_after_seconds": window_seconds,
            },
            headers={"Retry-After": str(window_seconds)},
        )


async def _get_redis_client():
    """Get Redis client if available."""
    try:
        import redis.asyncio as redis

        client = redis.from_url(settings.redis_url, decode_responses=True)
        # Test connection
        await client.ping()
        return client
    except Exception as e:
        logger.warning(f"Redis unavailable for rate limiting, using memory: {e}")
        return None


async def _check_rate_limit_redis(
    client,
    key: str,
    limit: int,
    window_seconds: int,
) -> bool:
    """
    Check rate limit using Redis.

    Uses a sliding window algorithm with Redis sorted sets.

    Args:
        client: Redis client
        key: Rate limit key (e.g., "admin:approve:user_id")
        limit: Maximum requests allowed
        window_seconds: Time window in seconds

    Returns:
        True if request is allowed, False if rate limit exceeded
    """
    import time

    now = time.time()
    window_start = now - window_seconds

    # Use a pipeline for atomic operations
    pipe = client.pipeline()

    # Remove old entries outside the window
    pipe.zremrangebyscore(key, 0, window_start)

    # Count current requests in window
    pipe.zcard(key)

    # Add current request
    pipe.zadd(key, {str(now): now})

    # Set expiry on the key
    pipe.expire(key, window_seconds)

    results = await pipe.execute()
    current_count = results[1]

    return current_count < limit


async def _check_rate_limit_memory(
    key: str,
    limit: int,
    window_seconds: int,
) -> bool:
    """
    Check rate limit using in-memory storage.

    Fallback when Redis is unavailable. Note: This doesn't work
    across multiple server instances.

    Args:
        key: Rate limit key
        limit: Maximum requests allowed
        window_seconds: Time window in seconds

    Returns:
        True if request is allowed, False if rate limit exceeded
    """
    import time

    now = time.time()
    window_start = now - window_seconds

    # Get or create entry list
    if key not in _memory_store:
        _memory_store[key] = []

    # Remove old entries
    _memory_store[key] = [(ts, count) for ts, count in _memory_store[key] if ts > window_start]

    # Count current requests
    current_count = sum(count for _, count in _memory_store[key])

    if current_count >= limit:
        return False

    # Add current request
    _memory_store[key].append((now, 1))

    return True


async def check_rate_limit(
    key: str,
    limit: int,
    window_seconds: int,
) -> bool:
    """
    Check if a request is within rate limits.

    Tries Redis first, falls back to in-memory storage.

    Args:
        key: Unique key for this rate limit (e.g., "admin:approve:user_123")
        limit: Maximum requests allowed in the window
        window_seconds: Time window in seconds

    Returns:
        True if request is allowed, False if rate limit exceeded
    """
    redis_client = await _get_redis_client()

    if redis_client:
        try:
            result = await _check_rate_limit_redis(redis_client, key, limit, window_seconds)
            await redis_client.close()
            return result
        except Exception as e:
            logger.warning(f"Redis rate limit check failed: {e}")
            await redis_client.close()

    # Fallback to memory
    return await _check_rate_limit_memory(key, limit, window_seconds)


def rate_limit(
    limit: int = 10,
    window_seconds: int = 60,
    key_func: Callable[[Request], str] | None = None,
):
    """
    Rate limiting decorator for FastAPI endpoints.

    Usage:
        @router.post("/approve")
        @rate_limit(limit=10, window_seconds=60)
        async def approve(request: Request, ...):
            ...

    Args:
        limit: Maximum requests allowed in the window (default: 10)
        window_seconds: Time window in seconds (default: 60)
        key_func: Optional function to generate rate limit key from request.
                  Default uses client IP + endpoint path.

    Raises:
        RateLimitExceeded: When rate limit is exceeded (HTTP 429)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Find request object in args or kwargs
            request: Request | None = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                request = kwargs.get("request")

            if not request:
                # No request object found, skip rate limiting
                logger.warning(
                    f"Rate limit decorator on {func.__name__} couldn't find Request object"
                )
                return await func(*args, **kwargs)

            # Generate rate limit key
            if key_func:
                key = key_func(request)
            else:
                # Default: IP + endpoint path
                client_ip = request.client.host if request.client else "unknown"
                key = f"rate_limit:{client_ip}:{request.url.path}"

            # Check rate limit
            allowed = await check_rate_limit(key, limit, window_seconds)

            if not allowed:
                logger.warning(f"Rate limit exceeded for {key}: {limit}/{window_seconds}s")
                raise RateLimitExceeded(limit, window_seconds)

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def admin_action_rate_limit(request: Request) -> str:
    """
    Generate rate limit key for admin actions.

    Uses admin user ID (from auth) + endpoint for precise limiting.
    Falls back to IP if user ID not available.

    Args:
        request: FastAPI request object

    Returns:
        Rate limit key string
    """
    # Try to get admin ID from request state (set by auth dependency)
    admin_id = getattr(request.state, "admin_id", None)

    if admin_id:
        return f"admin_action:{admin_id}:{request.url.path}"

    # Fallback to IP
    client_ip = request.client.host if request.client else "unknown"
    return f"admin_action:{client_ip}:{request.url.path}"


__all__ = [
    "rate_limit",
    "check_rate_limit",
    "admin_action_rate_limit",
    "RateLimitExceeded",
]
