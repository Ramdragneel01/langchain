from __future__ import annotations

import hashlib
import logging
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, Protocol

from fastapi import Request

from src.settings import Settings

try:
    import redis
except Exception:  # pragma: no cover
    redis = None


@dataclass
class RateLimitDecision:
    allowed: bool
    limit: int
    remaining: int
    reset_seconds: int
    retry_after_seconds: int | None = None


class RateLimiter(Protocol):
    def check(self, request: Request, settings: Settings) -> RateLimitDecision:
        ...

    @property
    def backend_name(self) -> str:
        ...


def _subject_key(request: Request, settings: Settings) -> str:
    api_key = request.headers.get(settings.api_key_header_name)
    if api_key:
        digest = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
        return f"api:{digest}"

    client_host = request.client.host if request.client else "unknown"
    return f"ip:{client_host}"


class InMemoryRateLimiter:
    def __init__(self, requests: int, window_seconds: int, key_prefix: str = "rrc") -> None:
        self.requests = requests
        self.window_seconds = window_seconds
        self.key_prefix = key_prefix
        self._hits: dict[str, Deque[float]] = {}
        self._lock = threading.Lock()

    @property
    def backend_name(self) -> str:
        return "memory"

    def check(self, request: Request, settings: Settings) -> RateLimitDecision:
        if not settings.rate_limit_enabled:
            return RateLimitDecision(
                allowed=True,
                limit=settings.rate_limit_requests,
                remaining=settings.rate_limit_requests,
                reset_seconds=settings.rate_limit_window_seconds,
            )

        key = f"{self.key_prefix}:{_subject_key(request=request, settings=settings)}"
        now = time.monotonic()
        window_start = now - self.window_seconds

        with self._lock:
            hits = self._hits.setdefault(key, deque())

            while hits and hits[0] <= window_start:
                hits.popleft()

            if len(hits) >= self.requests:
                oldest = hits[0]
                reset = max(1, int(self.window_seconds - (now - oldest)))
                return RateLimitDecision(
                    allowed=False,
                    limit=self.requests,
                    remaining=0,
                    reset_seconds=reset,
                    retry_after_seconds=reset,
                )

            hits.append(now)
            oldest = hits[0]
            remaining = max(0, self.requests - len(hits))
            reset = max(1, int(self.window_seconds - (now - oldest)))
            return RateLimitDecision(
                allowed=True,
                limit=self.requests,
                remaining=remaining,
                reset_seconds=reset,
            )


class RedisRateLimiter:
    _WINDOW_SCRIPT = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])

local current = redis.call('INCR', key)
if current == 1 then
  redis.call('EXPIRE', key, window)
end

local ttl = redis.call('TTL', key)
if ttl < 0 then
  ttl = window
end

local remaining = limit - current
if remaining < 0 then
  remaining = 0
end

if current > limit then
  return {0, limit, remaining, ttl}
end

return {1, limit, remaining, ttl}
""".strip()

    def __init__(
        self,
        requests: int,
        window_seconds: int,
        redis_url: str,
        socket_timeout_seconds: float,
        key_prefix: str = "rrc",
        redis_client=None,
    ) -> None:
        self.requests = requests
        self.window_seconds = window_seconds
        self.key_prefix = key_prefix

        if redis_client is not None:
            self._client = redis_client
        else:
            if redis is None:
                raise RuntimeError(
                    "redis package is not installed but RATE_LIMIT_BACKEND=redis"
                )
            self._client = redis.Redis.from_url(
                redis_url,
                socket_timeout=socket_timeout_seconds,
                socket_connect_timeout=socket_timeout_seconds,
                decode_responses=False,
            )

        try:
            self._client.ping()
        except Exception as exc:
            raise RuntimeError("unable_to_connect_to_redis_for_rate_limit") from exc

    def _check_without_lua(self, key: str) -> list[int]:
        current = int(self._client.incr(key))
        if current == 1:
            self._client.expire(key, self.window_seconds)
            ttl = self.window_seconds
        else:
            ttl = int(self._client.ttl(key))
            if ttl < 0:
                self._client.expire(key, self.window_seconds)
                ttl = self.window_seconds

        remaining = max(0, self.requests - current)
        allowed = 0 if current > self.requests else 1
        return [allowed, self.requests, remaining, max(1, ttl)]

    @property
    def backend_name(self) -> str:
        return "redis"

    def check(self, request: Request, settings: Settings) -> RateLimitDecision:
        if not settings.rate_limit_enabled:
            return RateLimitDecision(
                allowed=True,
                limit=settings.rate_limit_requests,
                remaining=settings.rate_limit_requests,
                reset_seconds=settings.rate_limit_window_seconds,
            )

        key = f"{self.key_prefix}:{_subject_key(request=request, settings=settings)}"
        try:
            raw = self._client.eval(
                self._WINDOW_SCRIPT,
                1,
                key,
                self.requests,
                self.window_seconds,
            )
        except Exception as exc:
            if "unknown command" in str(exc).lower() and "eval" in str(exc).lower():
                raw = self._check_without_lua(key=key)
            else:
                raise RuntimeError("redis_rate_limit_check_failed") from exc

        allowed = bool(int(raw[0]))
        limit = int(raw[1])
        remaining = int(raw[2])
        reset_seconds = max(1, int(raw[3]))

        return RateLimitDecision(
            allowed=allowed,
            limit=limit,
            remaining=remaining,
            reset_seconds=reset_seconds,
            retry_after_seconds=(reset_seconds if not allowed else None),
        )


def build_rate_limiter(
    settings: Settings, logger: logging.Logger | None = None
) -> RateLimiter:
    backend = settings.rate_limit_backend

    if backend == "memory":
        return InMemoryRateLimiter(
            requests=settings.rate_limit_requests,
            window_seconds=settings.rate_limit_window_seconds,
            key_prefix=settings.rate_limit_key_prefix,
        )

    if backend == "redis":
        try:
            return RedisRateLimiter(
                requests=settings.rate_limit_requests,
                window_seconds=settings.rate_limit_window_seconds,
                redis_url=settings.redis_url,
                socket_timeout_seconds=settings.redis_socket_timeout_seconds,
                key_prefix=settings.rate_limit_key_prefix,
            )
        except Exception:
            if settings.rate_limit_fail_open:
                if logger is not None:
                    logger.exception("redis_limiter_init_failed_falling_back_to_memory")
                return InMemoryRateLimiter(
                    requests=settings.rate_limit_requests,
                    window_seconds=settings.rate_limit_window_seconds,
                    key_prefix=settings.rate_limit_key_prefix,
                )
            raise

    raise ValueError(
        "RATE_LIMIT_BACKEND must be one of: memory, redis"
    )
