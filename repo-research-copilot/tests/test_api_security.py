from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src import api as api_module


class StubEngine:
    def ask(self, question: str, k: int | None = None) -> dict[str, object]:
        return {
            "answer": f"stub answer for: {question}",
            "sources": [
                {
                    "path": "README.md",
                    "chunk_id": "README.md::chunk-0",
                    "score": 0.99,
                    "excerpt": "stub excerpt",
                }
            ],
        }


@pytest.fixture(autouse=True)
def _reset_runtime(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("REQUIRE_API_KEY", "false")
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("API_KEYS", raising=False)
    monkeypatch.delenv("API_KEYS_FILE", raising=False)
    monkeypatch.setenv("API_KEY_HEADER_NAME", "X-API-Key")
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    monkeypatch.setenv("RATE_LIMIT_BACKEND", "memory")
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "2")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")
    monkeypatch.setenv("METRICS_ENABLED", "true")

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


def test_health_endpoint_is_open(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ask_requires_api_key_when_enabled(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("REQUIRE_API_KEY", "true")
    monkeypatch.setenv("API_KEY", "super-secret")
    api_module.get_runtime_settings.cache_clear()
    api_module.get_rate_limiter.cache_clear()

    payload = {"question": "Where is auth configured?", "k": 3}

    unauthorized = client.post("/ask", json=payload)
    assert unauthorized.status_code == 401

    wrong_key = client.post("/ask", json=payload, headers={"X-API-Key": "bad"})
    assert wrong_key.status_code == 401

    authorized = client.post(
        "/ask", json=payload, headers={"X-API-Key": "super-secret"}
    )
    assert authorized.status_code == 200
    assert "answer" in authorized.json()


def test_ask_accepts_rotated_keys(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("REQUIRE_API_KEY", "true")
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.setenv("API_KEYS", "old-key,new-key")
    api_module.get_runtime_settings.cache_clear()
    api_module.get_rate_limiter.cache_clear()

    payload = {"question": "Where is auth configured?", "k": 3}

    old_key_response = client.post(
        "/ask", json=payload, headers={"X-API-Key": "old-key"}
    )
    new_key_response = client.post(
        "/ask", json=payload, headers={"X-API-Key": "new-key"}
    )

    assert old_key_response.status_code == 200
    assert new_key_response.status_code == 200


def test_rate_limit_is_enforced(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("REQUIRE_API_KEY", "false")
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "2")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")
    api_module.get_runtime_settings.cache_clear()
    api_module.get_rate_limiter.cache_clear()

    payload = {"question": "test question", "k": 2}

    first = client.post("/ask", json=payload)
    second = client.post("/ask", json=payload)
    third = client.post("/ask", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429
    assert third.json()["detail"] == "rate_limit_exceeded"
    assert "Retry-After" in third.headers


def test_metrics_endpoint_available_by_default(client: TestClient):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "rrc_http_requests_total" in response.text
