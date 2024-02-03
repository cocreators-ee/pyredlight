import asyncio
import re
from dataclasses import dataclass
from typing import List, Tuple

from pyredlight.redis import get_redis

GLOBAL_PREFIX = "pyredlight"
LIMIT_TEST = re.compile("[0-9]+/[0-9]+[hms]")


@dataclass
class Limiter:
    count: int
    seconds: int
    prefix: str

    async def is_ok(self, key: str) -> Tuple[bool, int, int]:
        """
        Check if the key should be allowed through the limiter
        :param key:
        :return: ok, requests remaining, time until limit resets
        """
        redis = get_redis()
        real_key = f"{GLOBAL_PREFIX}_{self.prefix}_{key}"

        async with redis.pipeline() as pipe:
            # Set new key if it does not exist
            pipe = pipe.set(real_key, self.count, ex=self.seconds, nx=True)
            # Decrement and return current value
            pipe = pipe.decr(real_key)
            # Get remaining TTL for key in seconds
            pipe = pipe.ttl(real_key)
            _, decr, ttl = await pipe.execute()

            remaining = max(decr, 0)
            return decr >= 0, remaining, ttl

    async def clear(self, key: str):
        redis = get_redis()
        real_key = f"{GLOBAL_PREFIX}_{self.prefix}_{key}"

        await redis.delete(real_key)


class MergedLimiter:
    limiters: List[Limiter] = None

    def __init__(self, limiters: List[Limiter]):
        self.limiters = limiters

    async def is_ok(self, key):
        results = await asyncio.gather(
            *[limiter.is_ok(key) for limiter in self.limiters]
        )

        ok = True
        remaining = None
        ttl = None

        for r in results:
            _ok, _rem, _ttl = r
            if not _ok:
                ok = False

            if ttl is None or _rem < remaining:
                remaining = _rem
                ttl = _ttl

            # If we're at 0 requests allowed we want the largest time we need to wait for
            if ttl == 0 and _ttl == 0:
                if _rem > remaining:
                    remaining = _rem

        return ok, remaining, ttl

    async def clear(self, key):
        await asyncio.gather(*[limiter.clear(key) for limiter in self.limiters])


def parse_duration(duration_def) -> int:
    last = duration_def[-1]
    if last == "h":
        return int(duration_def[:-1]) * 3600
    elif last == "m":
        return int(duration_def[:-1]) * 60
    elif last == "s":
        return int(duration_def[:-1])
    raise ValueError(f"Invalid duration {duration_def}")


def limit(limit_def: str) -> Limiter:
    if LIMIT_TEST.fullmatch(limit_def) is None:
        raise ValueError(f"Invalid limit {limit_def}")

    count, duration_str = limit_def.split("/")
    seconds = parse_duration(duration_str)
    if seconds <= 0:
        raise ValueError(f"Invalid duration {duration_str}")

    return Limiter(count=count, seconds=seconds, prefix=limit_def)


def merge_limits(limits: List[Limiter]) -> MergedLimiter:
    return MergedLimiter(limits)
