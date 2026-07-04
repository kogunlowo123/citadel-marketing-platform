import time

import redis.asyncio as aioredis
import structlog

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class RateLimiter:
    def __init__(self, redis_url: str | None = None, key_prefix: str = "ratelimit"):
        self.redis = aioredis.from_url(redis_url or settings.REDIS_URL)
        self.key_prefix = key_prefix

    async def check_rate(self, key: str, max_per_minute: int) -> bool:
        """Token bucket rate limiter. Returns True if the request is allowed."""
        full_key = f"{self.key_prefix}:{key}"
        now = time.time()
        window_start = now - 60

        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(full_key, 0, window_start)
        pipe.zadd(full_key, {str(now): now})
        pipe.zcard(full_key)
        pipe.expire(full_key, 120)
        results = await pipe.execute()

        current_count = results[2]
        if current_count > max_per_minute:
            await self.redis.zrem(full_key, str(now))
            return False
        return True

    async def get_remaining(self, key: str, max_per_minute: int) -> int:
        """Get remaining allowed requests in the current window."""
        full_key = f"{self.key_prefix}:{key}"
        now = time.time()
        window_start = now - 60

        await self.redis.zremrangebyscore(full_key, 0, window_start)
        current = await self.redis.zcard(full_key)
        return max(0, max_per_minute - current)
