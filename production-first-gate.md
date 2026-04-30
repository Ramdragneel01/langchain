# Production Gate (Phase 0)

This gate is the implementation contract before any app is onboarded into the unified shell.

## Scope

- drift-watch
- llm-judge
- ragbench
- prompt-ops
- neuralscope
- config-forge
- interview-os
- mlops-sentinel
- agent-tracer
- agentic-research-assistant
- agentic-ui

## Required checks per app

1. Request correlation
- Backend propagates X-Request-ID from incoming requests or generates one.
- Backend returns X-Request-ID in every HTTP response.

2. Security headers
- Backend applies baseline security headers (at minimum X-Content-Type-Options and X-Frame-Options).
- HSTS remains environment controlled.

3. Health and readiness probes
- Backend supports /health and /ready.
- Backend also supports /healthz and /readyz aliases for compatibility.

4. Backend test baseline
- backend tests folder exists at `backend/tests` or `tests` based on repository layout.

5. Frontend accessibility baseline
- Frontend package includes eslint-plugin-jsx-a11y.
- Frontend package includes @testing-library/react.
- agentic-ui must include @storybook/addon-a11y and @testing-library/react.

## Automation

Run the Phase 0 gate auditor from workspace root:

powershell -ExecutionPolicy Bypass -File scripts/phase0-production-gate.ps1

Generate JSON report:

powershell -ExecutionPolicy Bypass -File scripts/phase0-production-gate.ps1 -Json

Exit code is non-zero when any repository fails the gate.

## Current implementation status

- Request ID propagation and probe alias standardization started across backend services.
- Frontend a11y dependency baseline enforcement is tracked by the gate script and will be applied in the next hardening slice.
