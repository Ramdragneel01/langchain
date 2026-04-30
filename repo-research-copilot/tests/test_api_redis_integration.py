from __future__ import annotations

import os

import pytest
import redis
from fastapi.testclient import TestClient

from src import api as api_module


class StubEngine:
    def ask(self, question: str, k: int | None = None) -> dict[str, object]:
        return {
            "answer": f"stub redis integration answer for: {question}",
            "sources": [
                {
                    "path": "README.md",
                    "chunk_id": "README.md::chunk-0",
                    "score": 0.9,
                    "excerpt": "stub excerpt",
                }
            ],
        }


@pytest.fixture(scope="module")
def redis_url() -> str:
    if os.getenv("RUN_REDIS_INTEGRATION") != "1":
        pytest.skip("Set RUN_REDIS_INTEGRATION=1 to run Redis integration tests")

    url = os.getenv("TEST_REDIS_URL", "redis://127.0.0.1:6379/0")
    client = redis.Redis.from_url(url, socket_timeout=1.0, socket_connect_timeout=1.0)
    try:
        client.ping()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"Redis integration unavailable: {exc}")

    client.flushdb()
    yield url
    try:
        client.flushdb()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def _configure(monkeypatch: pytest.MonkeyPatch, redis_url: str):
    monkeypatch.setenv("REQUIRE_API_KEY", "false")
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_BACKEND", "redis")
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "2")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")
    monkeypatch.setenv("RATE_LIMIT_FAIL_OPEN", "false")
    monkeypatch.setenv("REDIS_URL", redis_url)
    monkeypatch.setenv("REDIS_SOCKET_TIMEOUT_SECONDS", "1.0")

    api_module.get_runtime_settings.cache_clear()
    api_module.get_rate_limiter.cache_clear()
    api_module.get_engine.cache_clear()
    monkeypatch.setattr(api_module, "get_engine", lambda: StubEngine())

    yield

    api_module.get_runtime_settings.cache_clear()
    api_module.get_rate_limiter.cache_clear()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(api_module.app)


def test_redis_backed_rate_limit_is_enforced(client: TestClient):
    payload = {"question": "redis integration question", "k": 2}

    first = client.post("/ask", json=payload)
    second = client.post("/ask", json=payload)
    third = client.post("/ask", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429
    assert third.json()["detail"] == "rate_limit_exceeded"
    assert third.headers["X-RateLimit-Limit"] == "2"
