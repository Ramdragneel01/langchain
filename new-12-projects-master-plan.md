# Next-12 Production Projects — Foolproof Master Execution Plan

Owner: Ram Prakash Dhulipudi (`Ramdragneel01`)
Plan Date: 2026-04-30
Execution Model: **Strictly sequential within a phase, phases overlap only on writing/Medium tasks.**
Reuses the proven `pinworthy-8` production gate pattern.

---

## 0. Guiding Principles

1. **No scaffolds.** Every repo ends in a deployable, demo-able, recruiter-defensible state.
2. **One repo at a time** to production gate; parallelism is allowed only for Medium drafts.
3. **Every project ships with**: README, ARCHITECTURE.md, SECURITY.md, CHANGELOG.md, CODEOWNERS, CONTRIBUTING.md, Dockerfile, docker-compose.yml, GitHub Actions CI, tests (≥1 backend + ≥1 frontend if applicable), demo screenshot/GIF, and a deployed link or `make demo` path.
4. **Every project ships with one Medium article** (build log + lessons) within 7 days of repo push.
5. **No project starts** before the prior one passes the global production gate.

---

## 1. Global Production Gate (Must Pass Per Project)

Inherited from `pinworthy-8-projects-production-sequence.md` and extended:

| # | Gate | Evidence |
|---|---|---|
| 1 | Architecture documented | `ARCHITECTURE.md` + diagram in `docs/assets/` |
| 2 | Security baseline | `SECURITY.md`, input validation, headers, secret scanning |
| 3 | Deployable | Dockerfile + compose + cloud-deploy doc |
| 4 | CI green | `.github/workflows/ci.yml` running tests + build + container smoke |
| 5 | Release | Git tag + GHCR image OR npm/PyPI publish |
| 6 | Ops | `/health`, `/ready`, runbook in `docs/RUNBOOK.md` |
| 7 | Portfolio quality | README hero image, badges, 30-second demo path |
| 8 | **NEW — Medium article published** | Article URL captured in repo README |
| 9 | **NEW — dragon-portfolio updated** | Repo card added to `profileFallback.js` |

---

## 2. The 12 Projects — Tiered & Sequenced

### Tier 1 — Differentiator Closers (Phase A)
1. **rag-firewall** — Prompt injection / jailbreak defense gateway
2. **eval-harness-pro** — Continuous LLM eval GitHub Action + CLI
3. **agent-cost-governor** — FinOps / token budget router for agents
4. **vector-drift-monitor** — Embedding drift detection for RAG

### Tier 2 — Range Showcase (Phase B)
5. **copilot-for-readmes** — Auto README generator (CLI + VS Code ext)
6. **micro-frontend-starter-kit** — Module Federation + AI widgets
7. **gcp-vertex-rag-blueprint** — Vertex AI Search reference architecture
8. **speech-emotion-edge** — On-device SER via WASM/ONNX

### Tier 3 — Conversation Starters (Phase C)
9. **agent-replay** — Time-travel debugger for agents
10. **prompt-diff** — Semantic diff for prompts
11. **rag-for-codebases** — Self-hosted code Q&A bot
12. **certi-track** — Cert/learning roadmap tracker

---

## 3. Phased Execution Plan

> Each "Sprint" = one project to production gate + one Medium draft. Sprints are sequential.

### Phase A — "Close the Trust Stack" (Sprints 1–4)

| Sprint | Project | Stack | Key Deliverable | Medium Companion |
|---|---|---|---|---|
| A1 | rag-firewall | FastAPI + Llama Guard + OPA | Reverse proxy blocking 5 attack classes with live dashboard | "I built a prompt-injection firewall in a weekend" |
| A2 | eval-harness-pro | Python CLI + GitHub Action | PR-comment eval diffs (faithfulness, cost, latency) | "LLM unit tests as a service: continuous eval CI" |
| A3 | agent-cost-governor | FastAPI middleware + Redis | Token budget enforcement + auto-downgrade routing | "FinOps for AI agents: stop your $4k Friday" |
| A4 | vector-drift-monitor | Python + pgvector + Streamlit | Embedding drift detection + PSI on vector spaces | "Your RAG is rotting: detecting embedding drift" |

**Phase A Exit Criteria:** All 4 repos pinned on GitHub profile, 4 Medium articles live, dragon-portfolio updated.

---

### Phase B — "Prove the Range" (Sprints 5–8)

| Sprint | Project | Stack | Key Deliverable | Medium Companion |
|---|---|---|---|---|
| B1 | copilot-for-readmes | Node CLI + LLM + VS Code ext | Generate full production README from any repo | "I wrote a Copilot for READMEs and used it on 27 repos" |
| B2 | micro-frontend-starter-kit | Rspack/Webpack 5 MF + React | One-command MFE shell with 3 AI widgets | "Module Federation + AI widgets in 60 seconds" |
| B3 | gcp-vertex-rag-blueprint | Terraform + Vertex AI + Gemini | Deployable Vertex Search RAG reference + eval | "A production GCP RAG blueprint (Vertex AI Search + Gemini)" |
| B4 | speech-emotion-edge | ONNX + WASM + React | Browser-side emotion classifier from `speech-emotion-v2` | "Shrinking a speech emotion model to run in your browser" |

**Phase B Exit Criteria:** Recruiter-facing breadth proven (frontend + GCP + edge + tooling). Portfolio site lists 12 production repos.

---

### Phase C — "Conversation Starters" (Sprints 9–12)

| Sprint | Project | Stack | Key Deliverable | Medium Companion |
|---|---|---|---|---|
| C1 | agent-replay | Python + React DevTools-style UI | Record/replay agent runs with state diff | "Time-travel debugging for AI agents" |
| C2 | prompt-diff | Python CLI + embeddings | Semantic diff between two prompt versions | "git diff for prompts: a semantic approach" |
| C3 | rag-for-codebases | Python + tree-sitter + FAISS | AST-aware code Q&A with file:line citations | "I built a RAG that actually understands code" |
| C4 | certi-track | Next.js + SQLite/Supabase | Cert tracker with public profile pages | "Tracking 9 Google certs: lessons + a tool I built" |

**Phase C Exit Criteria:** 12/12 projects shipped, 12 Medium articles, profile rewritten with full narrative arc.

---

## 4. Per-Sprint Workflow (Reuse for Every Project)

Day-by-day template (calendar-free; gate-driven):

```
Step 1  Architecture spike      -> ARCHITECTURE.md + diagram
Step 2  Repo bootstrap          -> license, gitignore, dirs, package metadata
Step 3  Core MVP                -> end-to-end happy path locally working
Step 4  Tests                   -> backend pytest + frontend vitest where applicable
Step 5  Dockerize + compose     -> single `docker compose up` works
Step 6  CI                      -> GitHub Actions: lint, test, build, container smoke
Step 7  Security pass           -> input validation, headers, dependency scan
Step 8  Ops                     -> /health, /ready, RUNBOOK.md
Step 9  Demo evidence           -> screenshots/GIF, hosted demo or `make demo`
Step 10 Release                 -> git tag v0.1.0, GHCR/npm/PyPI publish
Step 11 Portfolio integration   -> add card to dragon-portfolio profileFallback.js
Step 12 Medium article          -> publish on medium.com/@RamPrakashD
Step 13 Production gate sign-off-> tick all 9 gates in tracker
```

Only after Step 13 do you start the next sprint.

---

## 5. Tracking

Create `c:\github_repos\new-12-projects-tracker.json` after kickoff with:
```json
{
  "rag-firewall": { "phase": "A1", "gates": { "1": false, "2": false, ... }, "mediumUrl": null },
  ...
}
```
This script can be reused at the end of each sprint to produce a green/red dashboard (same pattern as `phase0-production-gate-report.json`).

---

## 6. Medium Publishing Strategy

**Cadence:** 1 article per sprint — drafted on Day of Step 12, published within 48 hours.

**Series branding:** All 12 articles tagged with the series name **"Production AI, From Zero"** so they cross-link and compound SEO.

**Article skeleton (reuse for all 12):**
1. **Hook** — concrete pain in 2 sentences ("My agent ran $4k overnight…")
2. **What I built** — 1 paragraph + screenshot/GIF
3. **Architecture** — diagram + 3 bullets
4. **3 lessons that surprised me**
5. **Production gotchas**
6. **What's next**
7. **Repo link + demo link + LinkedIn CTA**

Drafts for the first 3 articles are committed to this workspace alongside this plan:
- `medium-drafts/01-rag-firewall.md`
- `medium-drafts/02-eval-harness-pro.md`
- `medium-drafts/03-gcp-vertex-rag-blueprint.md`

---

## 7. Risk Register & Mitigations

| Risk | Mitigation |
|---|---|
| Scope creep per sprint | Hard cap: if a sprint exceeds 1.5x estimated effort, descope features, never gates |
| Medium fatigue | Drafts are written in this repo first; publishing is a copy-paste step |
| Cloud cost (GCP blueprint) | Use free-tier Vertex quota; teardown script in repo; document daily cost cap |
| Dependency drift across 12 repos | Shared `.github` org-level reusable workflows; renovate bot enabled day 1 |
| LLM API key sprawl | Use one `.env.example` standard + 1 secrets manager (1Password CLI or doppler) |
| Burnout | One sprint = one project; no parallel coding work |

---

## 8. Definition of Done — The Whole Program

- [ ] 12 repos public, pinned, gate-passed
- [ ] 12 Medium articles published in the "Production AI, From Zero" series
- [ ] dragon-portfolio shows all 12 cards with live links
- [ ] LinkedIn featured section updated with top 4 (rag-firewall, eval-harness-pro, gcp-vertex-rag-blueprint, agent-replay)
- [ ] One pinned tweet/LinkedIn post linking the series
- [ ] Resume bullet added: "Shipped 12 production AI/MLOps projects with end-to-end CI/CD, observability, and published companion engineering essays."

---

## 9. Immediate Next Action (Today)

1. Approve this plan (or request edits).
2. Kick off **Sprint A1 — rag-firewall**:
   - Create `c:\github_repos\rag-firewall\` with the standard skeleton + ARCHITECTURE.md
   - Implement core middleware (FastAPI) blocking prompt-injection patterns
   - Stand up dashboard (React + Vite, reusing agentic-ui components)
3. While A1 is in flight, polish and publish the pre-drafted Medium article 1 once the demo screenshot exists.

End of plan.
