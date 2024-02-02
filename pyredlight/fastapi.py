from fastapi import Depends, HTTPException, Request

from pyredlight.limits import Limiter


async def default_get_key(request: Request):
    return request.client.host


def make_depends(limiter: Limiter, get_key=default_get_key):
    async def _depends(request: Request, key=Depends(get_key)):
        ok, remaining, expires = await limiter.is_ok(key)
        print("_depends", ok, remaining, expires)
        request.scope["rate_limit_remaining"] = remaining
        request.scope["rate_limit_expires"] = expires

        if not ok:
            raise HTTPException(429, "Rate limit exceeded")

    return _depends
