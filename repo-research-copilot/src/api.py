from __future__ import annotations

import logging
import time
import uuid
from functools import lru_cache

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.logging_utils import configure_structured_logging
from src.metrics import (
    REQUEST_INFLIGHT,
    inc_ask_outcome,
    inc_auth_failure,
    inc_rate_limit_block,
    metrics_response,
    record_request,
)
from src.rate_limit import RateLimitDecision, RateLimiter, build_rate_limiter
from src.retrieval import RepoResearchEngine
from src.security import authorize_request
from src.settings import Settings, load_settings
from src.tracing import configure_tracing

load_dotenv()
_bootstrap_settings = load_settings()
configure_structured_logging(_bootstrap_settings.log_level)

logger = logging.getLogger("repo_research.api")


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    k: int = Field(default=5, ge=1, le=20)


class SourceItem(BaseModel):
    path: str
    chunk_id: str
    score: float
    excerpt: str


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceItem]


app = FastAPI(
    title="Repo Research Copilot API",
    version="0.2.0",
    description="Production-hardened RAG API for repository Q&A with citations",
)
configure_tracing(app=app, settings=_bootstrap_settings)


@lru_cache(maxsize=1)
def get_runtime_settings() -> Settings:
    return load_settings()


@lru_cache(maxsize=1)
def get_rate_limiter() -> RateLimiter:
    return build_rate_limiter(settings=get_runtime_settings(), logger=logger)


@lru_cache(maxsize=1)
def get_engine() -> RepoResearchEngine:
    return RepoResearchEngine()


def _set_rate_limit_headers(response: Response, decision: RateLimitDecision) -> None:
    response.headers["X-RateLimit-Limit"] = str(decision.limit)
    response.headers["X-RateLimit-Remaining"] = str(decision.remaining)
    response.headers["X-RateLimit-Reset"] = str(decision.reset_seconds)


@app.middleware("http")
async def hardening_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    traceparent = request.headers.get("traceparent")
    start = time.perf_counter()
    path = request.url.path
    method = request.method
    client_ip = request.client.host if request.client else "unknown"
    settings = get_runtime_settings()

    rate_decision: RateLimitDecision | None = None
    rate_limiter_backend = "none"
    auth_key_fingerprint: str | None = None

    REQUEST_INFLIGHT.labels(method=method, path=path).inc()
    try:
        try:
            if path == "/ask":
                auth_key_fingerprint = authorize_request(
                    request=request,
                    settings=settings,
                )

                limiter = get_rate_limiter()
                rate_limiter_backend = limiter.backend_name
                try:
                    rate_decision = limiter.check(request=request, settings=settings)
                except Exception:
                    logger.exception(
                        "rate_limiter_runtime_error",
                        extra={
                            "extra_data": {
                                "request_id": request_id,
                                "method": method,
                                "path": path,
                                "backend": rate_limiter_backend,
                            }
                        },
                    )
                    if settings.rate_limit_fail_open:
                        rate_decision = RateLimitDecision(
                            allowed=True,
                            limit=settings.rate_limit_requests,
                            remaining=settings.rate_limit_requests,
                            reset_seconds=settings.rate_limit_window_seconds,
                        )
                    else:
                        response = JSONResponse(
                            status_code=503,
                            content={"detail": "rate_limiter_unavailable"},
                        )
                        response.headers["X-Request-ID"] = request_id
                        return response

                if not rate_decision.allowed:
                    response = JSONResponse(
                        status_code=429,
                        content={"detail": "rate_limit_exceeded"},
                    )
                    _set_rate_limit_headers(response=response, decision=rate_decision)
                    if rate_decision.retry_after_seconds is not None:
                        response.headers["Retry-After"] = str(
                            rate_decision.retry_after_seconds
                        )
                    response.headers["X-Request-ID"] = request_id
                    inc_rate_limit_block(rate_limiter_backend)

                    logger.warning(
                        "request_rate_limited",
                        extra={
                            "extra_data": {
                                "request_id": request_id,
                                "method": method,
                                "path": path,
                                "status_code": 429,
                                "client_ip": client_ip,
                                "rate_limiter_backend": rate_limiter_backend,
                            }
                        },
                    )
                    return response

            response = await call_next(request)
        except HTTPException as exc:
            if exc.status_code == 401:
                inc_auth_failure(str(exc.detail))
            response = JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
            )
        except Exception:
            logger.exception(
                "request_internal_error",
                extra={
                    "extra_data": {
                        "request_id": request_id,
                        "method": method,
                        "path": path,
                        "client_ip": client_ip,
                    }
                },
            )
            response = JSONResponse(
                status_code=500,
                content={"detail": "internal_server_error"},
            )

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        if rate_decision is not None:
            _set_rate_limit_headers(response=response, decision=rate_decision)

        record_request(
            method=method,
            path=path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        logger.info(
            "request_complete",
            extra={
                "extra_data": {
                    "request_id": request_id,
                    "traceparent": traceparent,
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "client_ip": client_ip,
                    "auth_key_fingerprint": auth_key_fingerprint,
                    "rate_limiter_backend": rate_limiter_backend,
                }
            },
        )
        return response
    finally:
        REQUEST_INFLIGHT.labels(method=method, path=path).dec()


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "repo-research-copilot",
    }


@app.get("/ready")
def ready() -> dict[str, str]:
    try:
        get_engine()
        get_rate_limiter()
    except Exception:
        logger.exception("engine_readiness_failed")
        raise HTTPException(status_code=503, detail="engine_not_ready")
    return {"status": "ready"}


@app.get(_bootstrap_settings.metrics_path, include_in_schema=False)
def metrics() -> Response:
    settings = get_runtime_settings()
    if not settings.metrics_enabled:
        raise HTTPException(status_code=404, detail="metrics_disabled")
    return metrics_response()


@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest) -> AskResponse:
    try:
        result = get_engine().ask(question=payload.question, k=payload.k)
    except FileNotFoundError:
        inc_ask_outcome("index_not_ready")
        raise HTTPException(status_code=503, detail="index_not_ready")
    except ValueError as exc:
        inc_ask_outcome("bad_request")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        inc_ask_outcome("internal_error")
        logger.exception("ask_request_failed")
        raise HTTPException(status_code=500, detail="internal_server_error")

    inc_ask_outcome("ok")
    return AskResponse(**result)
