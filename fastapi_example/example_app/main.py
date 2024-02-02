import redis.asyncio as redis
from fastapi import APIRouter, Depends, FastAPI, Request
from settings import REDIS_URL
from starlette.responses import JSONResponse

from pyredlight import limit, set_redis
from pyredlight.fastapi import make_depends

router = APIRouter()

per_minute_limit = limit("60/60s")


def get_rate_limit_key(request: Request):
    return request.client.host + "custom"


per_minute_depend = make_depends(per_minute_limit)
custom_key_example = make_depends(per_minute_limit, get_key=get_rate_limit_key)


@router.get("/")
async def get_data(_=Depends(per_minute_depend)):
    return JSONResponse({"status": "ok"})


@router.post("/")
async def set_data(_=Depends(custom_key_example)):
    return JSONResponse({"status": "ok"})


app = FastAPI()
app.include_router(router)


@app.middleware("http")
async def rate_limit_headers(request: Request, call_next):
    response = await call_next(request)
    rate_limit_remaining = request.scope.get("rate_limit_remaining", None)
    if rate_limit_remaining is not None:
        response.headers["X-Rate-Limit-Remains"] = str(
            request.scope["rate_limit_remaining"]
        )
        response.headers["X-Rate-Limit-Expires"] = str(
            request.scope["rate_limit_expires"]
        )
    return response


@app.on_event("startup")
async def setup():
    print(f"Setting up Redis connection to {REDIS_URL}")
    set_redis(redis.from_url(REDIS_URL))
