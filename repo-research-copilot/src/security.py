from __future__ import annotations

import hashlib
import hmac

from fastapi import HTTPException, Request, status

from src.settings import Settings


def _active_keys(settings: Settings) -> tuple[str, ...]:
    if settings.api_keys:
        return settings.api_keys
    if settings.api_key and settings.api_key.strip():
        return (settings.api_key.strip(),)
    return ()


def authorize_request(request: Request, settings: Settings) -> str | None:
    if not settings.require_api_key:
        return None

    expected_keys = _active_keys(settings)
    if not expected_keys:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="api_key_not_configured",
        )

    provided = request.headers.get(settings.api_key_header_name, "")
    for candidate in expected_keys:
        if hmac.compare_digest(provided, candidate):
            return hashlib.sha256(candidate.encode("utf-8")).hexdigest()[:16]

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="invalid_api_key",
    )
