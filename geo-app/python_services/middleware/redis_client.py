"""
Shared Redis client for caching, rate limiting, and task results.
"""
import os
import redis
from loguru import logger

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_redis_client = None


def get_redis() -> redis.Redis:
    """Get or create shared Redis connection."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            _redis_client.ping()
            logger.info(f"Redis connected: {REDIS_URL}")
        except redis.ConnectionError:
            logger.warning(f"Redis not available at {REDIS_URL}, using in-memory fallback")
            _redis_client = None
    return _redis_client


def is_redis_available() -> bool:
    """Check if Redis is available."""
    try:
        client = get_redis()
        return client is not None and client.ping()
    except Exception:
        return False
