from __future__ import annotations

import fakeredis
from starlette.requests import Request

from src.rate_limit import RedisRateLimiter
from src.settings import load_settings


def _request_with_key(api_key: str) -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/ask",
        "headers": [(b"x-api-key", api_key.encode("utf-8"))],
        "client": ("127.0.0.1", 50000),
    }
    return Request(scope)


def test_redis_rate_limiter_blocks_after_threshold(monkeypatch):
    monkeypatch.setenv("API_KEY_HEADER_NAME", "X-API-Key")
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "2")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")

    settings = load_settings()
    fake_redis = fakeredis.FakeRedis()

    limiter = RedisRateLimiter(
        requests=2,
        window_seconds=60,
        redis_url="redis://unused",
        socket_timeout_seconds=1.0,
        key_prefix="rrc-test",
        redis_client=fake_redis,
    )

    request = _request_with_key("rotated-key")
    first = limiter.check(request=request, settings=settings)
    second = limiter.check(request=request, settings=settings)
    third = limiter.check(request=request, settings=settings)

    assert first.allowed is True
    assert second.allowed is True
    assert third.allowed is False
    assert third.retry_after_seconds is not None
