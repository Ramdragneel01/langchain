# Pinworthy 8 Projects - Production to Deployment Sequence

Date: 2026-04-28
Owner: Ram Prakash Dhulipudi
Execution Model: Strictly sequential, each repo must pass production gate before moving to the next.

## Global Production Gate (Must Pass Per Project)

1. Architecture complete and documented (`ARCHITECTURE.md`).
2. Security baseline complete (`SECURITY.md`, input validation, security headers where applicable).
3. Deployment complete (Dockerfiles, compose profile, cloud deployment path).
4. CI complete (tests + build + container smoke).
5. Release complete (tag-based image publish and/or package publish).
6. Operations complete (health checks, readiness, runbook, alert playbook).
7. Portfolio quality complete (README clarity, demo path, recruiter-friendly evidence).

## Ordered Execution

1. drift-watch
2. llm-judge
3. agentic-ui
4. ragbench
5. prompt-ops
6. neuralscope
7. config-forge
8. interview-os

## Current Progress Snapshot

1. drift-watch: deployable baseline complete and validated (backend tests, frontend build, compose config).
2. llm-judge: deployable baseline complete and validated (backend tests, frontend build, compose config).
3. agentic-ui: deployable package baseline complete and validated (typecheck, vitest coverage, package build, Storybook build).
4. ragbench: deployable baseline complete and validated (backend tests, frontend build, compose config).
5. prompt-ops: deployable baseline complete and validated (backend tests, frontend build, compose config).
6. neuralscope: deployable baseline complete and validated (backend tests, frontend build, compose config, README screenshot).
7. config-forge: deployable baseline complete and validated (backend tests, frontend build, compose config, README screenshot).
8. interview-os: deployable baseline complete and validated (backend tests, frontend build, compose config, README screenshot).

All 8 projects in the planned sequence are now completed and pushed.

## Project 1: drift-watch (Completed and Built to Deployable Baseline)

### Final Product Shape

- Backend: FastAPI drift engine (PSI, KS, JS divergence)
- Frontend: React dashboard for schema + payload evaluation
- Deployment: Dockerized backend and frontend
- CI/CD: GitHub Actions for tests/build/release/pages

### Deployment Targets

- GHCR for container images
- Any managed container host (ECS/Cloud Run/AKS/Render)
- GitHub Pages for static frontend showcase

### Clarification Comment Strategy

- Keep non-obvious trade-offs in `docs/FUTURE-CLARIFICATIONS.md`.
- Add decision notes before changing scoring formulas or thresholds.
- Link PR descriptions to exact architecture decisions.

## Project 2: llm-judge (Baseline Implemented and Deployment-Ready)

### Service Topology

- Python API service for run orchestration
- Evaluator worker pool with provider adapters (OpenAI, Anthropic, Gemini)
- Storage for runs, metrics, and leaderboard snapshots
- React leaderboard and run drilldown UI

### Production Requirements

- Prompt and rubric versioning
- Provider rate-limit protection and retries
- Judge reproducibility controls (seeded settings where possible)
- Bias and safety guardrail checks

## Project 3: agentic-ui (Architecture Preview)

### Package Topology

- Monorepo with component package + docs app + Storybook
- Published npm package with semantic release
- Design tokens + accessibility-first component APIs

### Production Requirements

- Full keyboard support and WCAG AA checks
- Visual regression tests
- Tree-shakeable ESM builds and type-safe APIs

## Project 4: ragbench (Architecture Preview)

### Core Layers

- Benchmark runner engine
- Retrieval adapter interface (FAISS/Chroma/etc.)
- LLM answer evaluator + judge pipeline
- Report UI and exportable benchmark card

### Production Requirements

- Deterministic benchmark datasets
- Config snapshots for reproducibility
- Cost and latency accounting per run

## Project 5: prompt-ops (Architecture Preview)

### Core Layers

- Prompt registry with immutable versions
- Shadow traffic router for A/B variants
- Promotion policy engine
- Governance dashboard and rollback controls

### Production Requirements

- Audit log for prompt promotions
- Guardrails for unsafe prompt deployment
- Prompt lineage and experiment traceability

## Project 6: neuralscope (Architecture Preview)

### Core Layers

- Model graph extractor for PyTorch/TF
- Activation and gradient capture pipeline
- WebSocket channel for live run visualization
- Graph UI with heatmap overlays

### Production Requirements

- Efficient memory usage for large models
- Layer sampling controls to avoid browser overload
- Session capture export for reproducible debugging

## Project 7: config-forge (Architecture Preview)

### Core Layers

- JSON/YAML config interpreter
- Dynamic React renderer for forms/tables/dashboards
- LLM-assisted config generation endpoint
- Validation and policy enforcement layer

### Production Requirements

- Strict schema validation before render
- Safe expression handling (no arbitrary execution)
- Versioned configuration deployments

## Project 8: interview-os (Architecture Preview)

### Core Layers

- Next.js web app for interview flows
- Python voice pipeline (transcription and signal analysis)
- LLM evaluator for role-specific scoring
- Session analytics dashboard

### Production Requirements

- PII-sensitive data handling and retention controls
- Voice artifact encryption at rest
- Rubric calibration and anti-gaming checks

## One-by-One Execution Protocol

1. Design architecture and acceptance criteria.
2. Implement backend/frontend core.
3. Add deployment assets and CI/release workflows.
4. Validate health, test, and build gates.
5. Publish README demo evidence.
6. Only then start the next project.

## Clarification Comment Protocol (For Every Project)

1. Add one design note file under `docs/` for trade-offs.
2. Keep future changes listed in a dedicated clarification doc.
3. Add inline comments only where logic is non-obvious.
4. Keep decision rationale in PR descriptions and changelog.
