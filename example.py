import asyncio

import redis.asyncio as redis

from pyredlight import limit, set_redis

requests_per_minute = limit("60/60s")


def get_key(request):
    return f"rate_limit_example_{request['client_ip']}"


async def handle_request(request):
    key = get_key(request)
    ok, remaining, expires = await requests_per_minute.is_ok(key)
    if not ok:
        return {
            "status": 429,
            "rate_limit_remaining": remaining,  # Always 0
            "rate_limit_expires": expires,
        }
    else:
        return {
            "status": 200,
            "rate_limit_remaining": remaining,
            "rate_limit_expires": expires,
        }


async def main():
    for _ in range(10):
        print(await handle_request({"client_ip": "127.0.0.1"}))


if __name__ == "__main__":
    set_redis(redis.from_url("redis://your.redis.server"))
    asyncio.run(main())
