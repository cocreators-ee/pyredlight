import pytest
import fakeredis
from pyredlight import set_redis


@pytest.fixture(autouse=True)
async def set_fakeredis():
    set_redis(fakeredis.FakeAsyncRedis())
