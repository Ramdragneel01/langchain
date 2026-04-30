from __future__ import annotations

from fastapi import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

REQUEST_TOTAL = Counter(
    "rrc_http_requests_total",
    "Total HTTP requests handled by Repo Research Copilot",
    ["method", "path", "status_code"],
)
REQUEST_DURATION = Histogram(
    "rrc_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
REQUEST_INFLIGHT = Gauge(
    "rrc_http_requests_inflight",
    "Current in-flight requests",
    ["method", "path"],
)
AUTH_FAILURE_TOTAL = Counter(
    "rrc_auth_failures_total",
    "Authentication failures",
    ["reason"],
)
RATE_LIMIT_BLOCK_TOTAL = Counter(
    "rrc_rate_limit_block_total",
    "Requests blocked by rate limiting",
    ["backend"],
)
ASK_TOTAL = Counter(
    "rrc_ask_total",
    "Total ask endpoint outcomes",
    ["result"],
)


def record_request(method: str, path: str, status_code: int, duration_ms: float) -> None:
    REQUEST_TOTAL.labels(method=method, path=path, status_code=str(status_code)).inc()
    REQUEST_DURATION.labels(method=method, path=path).observe(max(duration_ms, 0.0) / 1000.0)


def inc_auth_failure(reason: str) -> None:
    AUTH_FAILURE_TOTAL.labels(reason=reason).inc()


def inc_rate_limit_block(backend: str) -> None:
    RATE_LIMIT_BLOCK_TOTAL.labels(backend=backend).inc()


def inc_ask_outcome(result: str) -> None:
    ASK_TOTAL.labels(result=result).inc()


def metrics_response() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
