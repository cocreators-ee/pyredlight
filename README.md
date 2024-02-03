# PyRedLight

[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/cocreators-ee/pyredlight/publish.yaml)](https://github.com/cocreators-ee/pyredlight/actions/workflows/publish.yaml)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Security: bandit](https://img.shields.io/badge/security-bandit-green.svg)](https://github.com/PyCQA/bandit)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/cocreators-ee/pyredlight/blob/master/.pre-commit-config.yaml)
[![PyPI](https://img.shields.io/pypi/v/pyredlight)](https://pypi.org/project/pyredlight/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyredlight)](https://pypi.org/project/pyredlight/)
[![License: BSD 3-Clause](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

Rate limiting for Python with fast Redis transactions.

Simply put, instead of running multiple individual operations leading to multiple round-trips to your Redis server, we
execute a small transaction consisting of the following commands (for a limit of `60/10s`)

```
SET key 60 EX 10 NX   # Create key and set expiration time, if it does not exist
DECR key              # Decrement value and return
TTL key               # Return time until key expires
```

Then from the results we parse how many requests you're still allowed to perform within the limit (if any), and what is
the expiration time for the request window.

Also contains utilities and examples for convenient use with FastAPI.

## Installation

It's a Python library, what do you expect?

```bash
pip install pyredlight
# OR
poetry add pyredlight
```

## Usage

If you want to test the examples make sure you replace `redis://your.redis.server` with an actual connect string.

Limits can be defined using the format `{requests}/{time}[hms]`, so `100/10s` = 100 requests / 10 seconds, `60/1m` = 60
requests / minute, `5000/6h` = 5000 requests / 6 hours.

Small example of how you can use this library (also in [example.py](./example.py), test
with `poetry install && poetry run python example.py`):

```python
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
```

Or in FastAPI (also in [fastapi_example](./fastapi_example), test
with `cd fastapi_example && poetry install && poetry run python example.py`):

```python
from fastapi import FastAPI, Request, APIRouter, Depends
from starlette.responses import JSONResponse

from pyredlight import limit, set_redis
from pyredlight.fastapi import make_depends

import redis.asyncio as redis

per_minute_limit = limit("60/60s")


def get_rate_limit_key(request: Request):
  return request.client.host + "custom"


per_minute_depend = make_depends(per_minute_limit)
custom_key_example = make_depends(per_minute_limit, get_key=get_rate_limit_key)

router = APIRouter()


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
    response.headers["X-Rate-Limit-Remains"] = str(request.scope["rate_limit_remaining"])
    response.headers["X-Rate-Limit-Expires"] = str(request.scope["rate_limit_expires"])
  return response


@app.on_event("startup")
async def setup():
  set_redis(redis.from_url("redis://your.redis.server"))
```

For the rare cases you might want to reset a limit, you can also `.clear(key)` instead of `.is_ok(key)`.

You may also occasionally find it useful to merge limits, to e.g. check `20/1s` and `50/1m` at the same time, for that
there's a helper:

```python
from pyredlight import limit, merge_limits

per_second_limit = limit("20/1s")
per_minute_limit = limit("50/1m")
combined_limit = merge_limits([per_second_limit, per_minute_limit])


async def example():
  ok, remaining, expires = await combined_limit.is_ok("key")
```

The return value from `merge_limits` implements the same interface as `limit`, so you can also `.clear()` keys - which
will then be cleared from all the limits.

## Performance

You should really not expect much extra latency beyond a single network RTT to your Redis server for each check, as long
as your Redis server is capable of handling the requests. With a very simple Redis server in the same LAN
as [benchmark.py](./benchmark.py) it seems each call is taking approx 110-150μsec.

## Development

Issues and PRs are welcome!

Please open an issue first to discuss the idea before sending a PR so that you know if it would be wanted or needs
re-thinking or if you should just make a fork for yourself.

For local development, make sure you install [pre-commit](https://pre-commit.com/#install), then run:

```bash
pre-commit install
poetry install
poetry run pytest-watch
poetry run python example.py

cd fastapi_example
poetry run python example.py
```

## License

The code is released under the BSD 3-Clause license. Details in the [LICENSE.md](./LICENSE.md) file.

# Financial support

This project has been made possible thanks to [Cocreators](https://cocreators.ee) and [Lietu](https://lietu.net). You
can help us continue our open source work by supporting us
on [Buy me a coffee](https://www.buymeacoffee.com/cocreators).

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/cocreators)
