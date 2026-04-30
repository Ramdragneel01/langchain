from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int, minimum: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = int(raw)
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


def _env_float(name: str, default: float, minimum: float, maximum: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = float(raw)
    if value < minimum or value > maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return value


def _split_key_values(raw: str) -> list[str]:
    parts = [segment.strip() for segment in raw.replace("\n", ",").split(",")]
    return [part for part in parts if part]


def _dedupe_preserve_order(values: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return tuple(result)


def _load_api_keys() -> tuple[str, ...]:
    values: list[str] = []

    api_keys_env = os.getenv("API_KEYS", "")
    if api_keys_env:
        values.extend(_split_key_values(api_keys_env))

    # Backward-compatible single key support.
    api_key_env = os.getenv("API_KEY", "")
    if api_key_env.strip():
        values.append(api_key_env.strip())

    keys_file = os.getenv("API_KEYS_FILE")
    if keys_file:
        path = Path(keys_file)
        if path.exists():
            file_text = path.read_text(encoding="utf-8", errors="ignore")
            values.extend(_split_key_values(file_text))

    return _dedupe_preserve_order(values)


@dataclass(frozen=True)
class Settings:
    embedding_provider: str
    embedding_dim: int
    openai_chat_model: str
    openai_embedding_model: str
    use_openai_chat: bool
    index_path: Path
    top_k: int
    chunk_size: int
    chunk_overlap: int
    require_api_key: bool
    api_key: str | None
    api_keys: tuple[str, ...]
    api_key_header_name: str
    rate_limit_enabled: bool
    rate_limit_backend: str
    rate_limit_requests: int
    rate_limit_window_seconds: int
    rate_limit_key_prefix: str
    rate_limit_fail_open: bool
    redis_url: str
    redis_socket_timeout_seconds: float
    metrics_enabled: bool
    metrics_path: str
    tracing_enabled: bool
    tracing_service_name: str
    otel_exporter_otlp_endpoint: str | None
    otel_sampler_ratio: float
    log_level: str


def load_settings() -> Settings:
    api_keys = _load_api_keys()
    return Settings(
        embedding_provider=os.getenv("EMBEDDING_PROVIDER", "hash").strip().lower(),
        embedding_dim=_env_int("EMBEDDING_DIM", 256, 16),
        openai_chat_model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini"),
        openai_embedding_model=os.getenv(
            "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
        ),
        use_openai_chat=_env_bool("USE_OPENAI_CHAT", False),
        index_path=Path(os.getenv("INDEX_PATH", "data/index")),
        top_k=_env_int("TOP_K", 5, 1),
        chunk_size=_env_int("CHUNK_SIZE", 1200, 100),
        chunk_overlap=_env_int("CHUNK_OVERLAP", 200, 0),
        require_api_key=_env_bool("REQUIRE_API_KEY", True),
        api_key=os.getenv("API_KEY"),
        api_keys=api_keys,
        api_key_header_name=os.getenv("API_KEY_HEADER_NAME", "X-API-Key"),
        rate_limit_enabled=_env_bool("RATE_LIMIT_ENABLED", True),
        rate_limit_backend=os.getenv("RATE_LIMIT_BACKEND", "memory").strip().lower(),
        rate_limit_requests=_env_int("RATE_LIMIT_REQUESTS", 60, 1),
        rate_limit_window_seconds=_env_int("RATE_LIMIT_WINDOW_SECONDS", 60, 1),
        rate_limit_key_prefix=os.getenv("RATE_LIMIT_KEY_PREFIX", "rrc"),
        rate_limit_fail_open=_env_bool("RATE_LIMIT_FAIL_OPEN", True),
        redis_url=os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0"),
        redis_socket_timeout_seconds=_env_float(
            "REDIS_SOCKET_TIMEOUT_SECONDS", 1.5, 0.1, 10.0
        ),
        metrics_enabled=_env_bool("METRICS_ENABLED", True),
        metrics_path=os.getenv("METRICS_PATH", "/metrics"),
        tracing_enabled=_env_bool("TRACING_ENABLED", False),
        tracing_service_name=os.getenv("TRACING_SERVICE_NAME", "repo-research-copilot"),
        otel_exporter_otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
        otel_sampler_ratio=_env_float("OTEL_SAMPLER_RATIO", 0.2, 0.0, 1.0),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )
