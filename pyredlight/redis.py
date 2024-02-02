from typing import Optional

import redis.asyncio as redis

_REDIS_CLIENT: Optional[redis.Redis] = None


def set_redis(redis_client: redis.Redis):
    global _REDIS_CLIENT
    _REDIS_CLIENT = redis_client


def get_redis() -> redis.Redis:
    global _REDIS_CLIENT
    if not _REDIS_CLIENT:
        raise ValueError("No Redis client set")
    return _REDIS_CLIENT
