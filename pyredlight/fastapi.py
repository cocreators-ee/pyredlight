from fastapi import Depends, HTTPException, Request
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from pyredlight.limits import Limiter


async def default_get_key(request: Request):
    return request.client.host


def make_depends(
    limiter: Limiter,
    get_key=default_get_key,
    retry_after_header: bool = True,
):
    async def _depends(request: Request, key=Depends(get_key)):
        ok, remaining, expires = await limiter.is_ok(key)
        request.scope["rate_limit_remaining"] = remaining
        request.scope["rate_limit_expires"] = expires

        headers = None
        if retry_after_header:
            headers = {
                "Retry-After": str(expires),
            }

        if not ok:
            raise HTTPException(
                HTTP_429_TOO_MANY_REQUESTS,
                "Rate limit exceeded",
                headers=headers,
            )

    return _depends
