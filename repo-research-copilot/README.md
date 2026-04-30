# Repo Research Copilot

LangChain-based repository Q&A assistant with source citations.

This project is optimized for your main objective: quickly shipping a practical portfolio project that demonstrates reusable RAG/agent engineering workflows, not one-off scripts.

## Production Hardening (Phase 1)
This repository now includes a baseline production hardening layer:
1. API key authentication on `/ask`.
2. Request rate limiting on `/ask`.
3. Structured JSON request logs with request IDs.
4. Docker container image for API deployment.
5. Pytest security/rate-limit tests.
6. GitHub Actions CI workflow.

## Production Hardening (Phase 2)
This repository now also includes:
1. Redis-backed distributed rate limiting option.
2. API key rotation support with multiple active keys.
3. Prometheus metrics endpoint.
4. Optional OpenTelemetry tracing instrumentation.
5. Container base-image policy enforcement with digest pinning.
6. Container vulnerability gate in CI.
7. Docker Compose profile for one-command local phase-2 stack.
8. CI matrix plus Redis service integration test job.

## What It Does
1. Indexes docs and code from a target repository.
2. Builds embeddings and a local similarity index.
3. Serves a question-answer API with source citations.
4. Provides a Streamlit UI for interactive demos.
5. Includes a smoke evaluation script for repeatability.

## Default Wiring
The default smoke flow is designed around:
1. Source repo: `C:/github_repos/agentic-research-assistant`
2. Index output: `data/index`
3. API: `http://127.0.0.1:8010`

## Setup
```powershell
Set-Location C:/github_repos/repo-research-copilot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env -Force
```

For local development tests:
```powershell
pip install -r requirements-dev.txt
```

## Build Index
```powershell
python -m src.ingest --repo-path C:/github_repos/agentic-research-assistant --out-index data/index
```

## Run API
```powershell
uvicorn src.api:app --reload --port 8010
```

The `/ask` endpoint requires an API key by default.
Use header `X-API-Key: <your API_KEY value>`.

For key rotation, configure multiple keys with `API_KEYS`:
```text
API_KEYS=old-key,new-key,next-key
```

## Run UI
```powershell
streamlit run ui/app.py --server.port 8511
```

## Smoke Eval
```powershell
python -m eval.run_eval --api-url http://127.0.0.1:8010 --questions eval/questions.json --api-key change-me
```

If your API uses a custom auth header, also pass:
```powershell
python -m eval.run_eval --api-url http://127.0.0.1:8010 --questions eval/questions.json --api-key change-me --api-key-header X-API-Key
```

## Run Tests
```powershell
pytest -q
```

## Redis-backed Rate Limit
Switch from in-memory to distributed limiter:
```text
RATE_LIMIT_BACKEND=redis
REDIS_URL=redis://127.0.0.1:6379/0
RATE_LIMIT_REQUESTS=120
RATE_LIMIT_WINDOW_SECONDS=60
```

If Redis is unavailable and `RATE_LIMIT_FAIL_OPEN=true`, middleware falls back to memory limiter.

## Metrics and Tracing
Prometheus metrics endpoint (enabled by default):
1. Path: `/metrics`
2. Enable/disable with `METRICS_ENABLED`

Tracing:
1. Enable with `TRACING_ENABLED=true`
2. Configure exporter with `OTEL_EXPORTER_OTLP_ENDPOINT`
3. Tune sampling with `OTEL_SAMPLER_RATIO`

## Docker
Build image:
```powershell
docker build -t repo-research-copilot:latest .
```

Run container:
```powershell
docker run --rm -p 8010:8010 --env-file .env -v ${PWD}/data/index:/app/data/index repo-research-copilot:latest
```

## Docker Compose (Phase 2 One Command)
Bring up API + Redis + OTEL Collector + Jaeger:
```powershell
Copy-Item .env.example .env -Force
docker compose --profile phase2 up --build
```

Endpoints:
1. API: `http://localhost:8010`
2. Metrics: `http://localhost:8010/metrics`
3. Jaeger UI: `http://localhost:16686`

Notes:
1. API expects indexed data mounted from `./data/index`.
2. Compose uses `RATE_LIMIT_BACKEND=redis` and sends traces to OTEL collector.

## Strict Container Policy
Container hardening files:
1. Policy catalog: `security/base-image-policy.json`
2. Policy check script: `scripts/enforce_container_policy.py`

Run policy check locally:
```powershell
python scripts/enforce_container_policy.py
```

CI also builds and vulnerability-scans the image (high/critical gate).

## CI Matrix and Redis Integration
CI now runs:
1. Matrix test job for limiter modes (`memory`, `redis` unit suite).
2. Redis integration job using a Redis service container.
3. Container policy + vulnerability gate job.

## Environment Variables (Security and Ops)
From `.env.example`:
1. `REQUIRE_API_KEY`: Require API key on `/ask`.
2. `API_KEY`: Shared secret key.
3. `API_KEY_HEADER_NAME`: Header name used for API key.
4. `RATE_LIMIT_ENABLED`: Enable/disable rate limiting.
5. `RATE_LIMIT_REQUESTS`: Allowed requests per window.
6. `RATE_LIMIT_WINDOW_SECONDS`: Window size in seconds.
7. `LOG_LEVEL`: API log level.
8. `API_KEYS`: Comma-separated active keys for rotation.
9. `API_KEYS_FILE`: Optional file path with active keys.
10. `RATE_LIMIT_BACKEND`: `memory` or `redis`.
11. `REDIS_URL`: Redis connection URL for distributed limiter.
12. `METRICS_ENABLED`: Enables Prometheus endpoint.
13. `TRACING_ENABLED`: Enables OpenTelemetry instrumentation.

## Embedding Modes
By default, `.env.example` uses local deterministic hash embeddings (`EMBEDDING_PROVIDER=hash`) so smoke tests run without external API keys.

To use OpenAI embeddings:
1. Set `EMBEDDING_PROVIDER=openai`
2. Export `OPENAI_API_KEY`

To use OpenAI chat answers:
1. Set `USE_OPENAI_CHAT=true`
2. Export `OPENAI_API_KEY`

## API Contract
`POST /ask`

Request:
```json
{
  "question": "Where is API routing initialized?",
  "k": 5
}
```

Required header when `REQUIRE_API_KEY=true`:
```text
X-API-Key: change-me
```

Response:
```json
{
  "answer": "...",
  "sources": [
    {
      "path": "api/main.py",
      "chunk_id": "api/main.py::chunk-0",
      "score": 0.5021,
      "excerpt": "..."
    }
  ]
}
```
