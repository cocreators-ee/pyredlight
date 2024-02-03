import secrets

import pytest

from pyredlight import limit, merge_limits


async def test_limit():
    limiter = limit("1/10s")
    key = "key_" + secrets.token_urlsafe(16)

    ok, _, _ = await limiter.is_ok(key)
    assert ok

    ok, _, _ = await limiter.is_ok(key)
    assert not ok

    await limiter.clear(key)

    ok, _, _ = await limiter.is_ok(key)
    assert ok

    ok, _, _ = await limiter.is_ok(key)
    assert not ok

    ok, _, _ = await limiter.is_ok(f"{key}2")
    assert ok


async def test_parse_limit():
    limiter1 = limit("10/100s")
    limiter2 = limit("10/10m")
    limiter3 = limit("10/2h")

    assert limiter1.seconds == 100
    assert limiter2.seconds == 600
    assert limiter3.seconds == 7200

    errors = [
        "/100s",
        "10/",
        "",
        "10/100",
        "10/1d",
        "10/1d",
        "10/-1s",
        "10/0s",
    ]

    for err in errors:
        with pytest.raises(ValueError):
            limit(err)


async def test_merge_limit():
    first = limit("1/10s")
    second = limit("1/50s")
    merged = merge_limits([first, second])

    key = "merge_test_key_" + secrets.token_urlsafe(16)

    ok, _, _ = await merged.is_ok(key)
    assert ok

    ok, _, _ = await merged.is_ok(key)
    assert not ok

    await first.clear(key)

    ok, _, _ = await merged.is_ok(key)
    assert not ok

    await first.clear(key)
    await second.clear(key)

    ok, _, _ = await merged.is_ok(key)
    assert ok
