import asyncio
import sys
import time

import redis.asyncio as redis

from pyredlight import limit, set_redis

requests_per_minute = limit("600/60s")
TEST_ROUNDS = 10_000


async def limited():
    ok, remaining, expires = await requests_per_minute.is_ok("limited")
    return {"ok": ok, "remaining": remaining, "expires": expires}


async def not_limited():
    return {"ok": True, "remaining": 999, "expires": 999}


async def benchmark(func) -> float:
    start = time.perf_counter()
    for _ in range(TEST_ROUNDS):
        await func()
    end = time.perf_counter()
    return end - start


async def main():
    limited_time = await benchmark(limited)
    not_limited_time = await benchmark(not_limited)
    diff = limited_time - not_limited_time
    diff_per_call = diff / TEST_ROUNDS

    print(f"Not limited: {not_limited_time:.6f}s")
    print(f"Limited: {limited_time:.6f}s")
    print(f"Diff: {diff}s / {TEST_ROUNDS} calls")
    print(f"Per call: {diff_per_call:.6f}s")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} redis://your.redis.server")
        raise sys.exit(1)
    redis_server = sys.argv[1]
    set_redis(redis.from_url(redis_server))
    asyncio.run(main())
