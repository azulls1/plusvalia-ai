"""
Redis-backed prediction cache. Falls back to in-memory LRU if Redis unavailable.
"""
import json
import time
from collections import OrderedDict
from loguru import logger
from middleware.redis_client import get_redis, is_redis_available


class PredictionCache:
    """Hybrid cache: Redis primary, in-memory fallback."""

    PREFIX = "pred_cache:"
    DEFAULT_TTL = 300  # 5 minutes

    def __init__(self, max_memory_size=500, ttl=300):
        self.ttl = ttl
        self._memory_cache = OrderedDict()
        self._memory_timestamps = {}
        self.max_memory_size = max_memory_size

    def get(self, key: str) -> dict | None:
        """Get cached prediction."""
        redis = get_redis()
        if redis:
            try:
                data = redis.get(f"{self.PREFIX}{key}")
                if data:
                    return json.loads(data)
            except Exception:
                pass

        # Fallback to memory
        if key in self._memory_cache:
            if time.time() - self._memory_timestamps.get(key, 0) > self.ttl:
                del self._memory_cache[key]
                del self._memory_timestamps[key]
                return None
            self._memory_cache.move_to_end(key)
            return self._memory_cache[key]
        return None

    def set(self, key: str, value: dict):
        """Store prediction in cache."""
        redis = get_redis()
        if redis:
            try:
                redis.set(f"{self.PREFIX}{key}", json.dumps(value), ex=self.ttl)
                return
            except Exception:
                pass

        # Fallback to memory
        if len(self._memory_cache) >= self.max_memory_size:
            self._memory_cache.popitem(last=False)
        self._memory_cache[key] = value
        self._memory_timestamps[key] = time.time()

    def clear(self):
        """Clear all cached predictions."""
        redis = get_redis()
        if redis:
            try:
                keys = redis.keys(f"{self.PREFIX}*")
                if keys:
                    redis.delete(*keys)
            except Exception:
                pass
        self._memory_cache.clear()
        self._memory_timestamps.clear()

    @property
    def size(self) -> int:
        redis = get_redis()
        if redis:
            try:
                return len(redis.keys(f"{self.PREFIX}*"))
            except Exception:
                pass
        return len(self._memory_cache)
