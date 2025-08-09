## Task Breakdown — Multi-Agent Deployment System (Hackathon MVP)

This plan maps your proposed agents/components to the current PRD and breaks work into owner-sized tasks with clear deliverables. Priorities: P0 (MVP), P1 (nice-to-have), P2 (stretch).

### Agent/Component Mapping
- Architect ↔ ArchitectAgent (PRD); plus P1: generate Vercel configs/CI (no Docker)
- DependencyAnalyzer ↔ DependencyAnalyzer (PRD); add outdated scan (npm/pip) and GitHub dependency graph (P1)
- PackageManager ↔ merge into ArchitectAgent (plan Vercel configs) + DeploymentAgent (apply); separate only if time allows (P2). No containerization.
- TestSuite ↔ TestSuiteAgent (PRD)
- DeploymentCoordinator ↔ Orchestrator (PRD)
- IncidentInvestigator/Monitor ↔ IncidentMonitorAgent (merged health + incidents; P1)
- Bot/App + Status updates ↔ FastAPI backend + GitHub Checks/Statuses (P1)
- TrafficManager (canary) ↔ stretch via Vercel API/aliases (P2)

---

### Tasks (Unified Backlog)

P0 — MVP
- Core
  - BaseAgent (ReAct skeleton); common tool helpers (fs scan, subprocess, http)
  - Orchestrator: sequential execution, context passing, WS broadcasts, fail-fast
  - AgentOps Replay: capture step events (LLM I/O, tool calls, stages) to an in-memory buffer (bounded)
- Backend/API
  - FastAPI app with `POST /webhook/github` + HMAC-SHA256 verification
  - Background task to trigger orchestration
- WebSocket manager and `/ws/status?deployment_id=...`
  - Skip REST status endpoints in MVP (WS only)
- Agents
  - ArchitectAgent: detect Node/Python, entrypoint, build command heuristics
  - DependencyAnalyzer: parse `package.json`/`requirements.txt`; normalize npm/pip
  - TestSuiteAgent: run `npm test` or `pytest` with timeout; capture output; skip if none
  - DeploymentAgent: Vercel CLI (`--token --yes --confirm`); parse `deployment_url`
- IncidentMonitorAgent: HTTP poll with basic retries/backoff; detect incidents/policy violations; notify and propose fixes; optional GitHub Issue/PR
- Frontend
  - Next.js dashboard: `/deployments/[id]` timeline UI; WebSocket client; render stage/log snippets

P1 — Nice to have
- GitHub Checks/Statuses integration for stage updates
- Outdated dependency scan: `npm outdated` / `pip list --outdated`
- Generate `vercel.json` and CI YAML if missing (no Docker)
- Improved retries/backoff in deploy/monitor; clearer error surfacing
- Structured logging; correlation by `deployment_id`
- Dashboard list view and WS auto-reconnect

P2 — Stretch
- TrafficManager: Vercel alias/canary management
- GitHub App packaging/installation
- IncidentInvestigator enhancements: auto-create GitHub Issue, git blame mentions, email/slack
- Separate PackageManager to optimize Vercel configs

---

### P0 Execution Steps (Assistant-run sequence)

1) Orchestrator skeleton
   - Create `orchestrator.py` with: `run_pipeline(repo_url, commit_sha, deployment_id)`; clones repo to temp dir; emits stage events via a broadcast callback; sequential context passing.

2) WebSocket manager
   - Create `realtime/ws.py` with connection registry and `broadcast(deployment_id, message)`.

3) FastAPI app stub
   - Create `api.py` with `POST /webhook/github` (HMAC-SHA256 verify) and background task to call orchestrator.
   - Add `/ws/status` endpoint hooking into `realtime/ws.py` and send buffered events on connect.
   - Add `GET /replay/{deployment_id}` to return recorded events (JSON array).

4) ArchitectAgent (minimal)
   - `agents/architect.py`: detect Node vs Python, set `project_type`, `entrypoint`, and basic build/install commands; optional `vercel.json` emission.

5) DependencyAnalyzer (minimal)
   - `agents/deps.py`: parse `package.json` or `requirements.txt`; set `dependencies`, `package_manager` (npm/pip).

6) TestSuiteAgent (minimal)
   - `agents/tests.py`: run `npm test` or `pytest` with timeout; capture output; set `tests_passed`.

7) DeploymentAgent
   - `agents/deployment.py`: invoke `vercel --token $VERCEL_TOKEN --yes --confirm` and parse `deployment_url` from stdout.

8) IncidentMonitorAgent (merged)
   - `agents/incident_monitor.py`: poll `deployment_url` with retries/backoff; set `healthy`; subscribe to status/trace; emit incidents/proposals; optional GitHub Issue/PR.

9) Wire orchestrator to agents
   - Execute in order: architect → deps → test → deploy → monitor; broadcast after each.
  - Also append each event to replay buffer (same payload as WS).
  - Add step-level trace events from agents via callbacks.

11) Replay API
  - `GET /replay/{deployment_id}` returns recorded events (already in place)
  - `POST /replay/{deployment_id}/broadcast?speed=1.0` replays the recorded timeline with timing

10) Env validation
   - On app startup, validate presence of `GITHUB_WEBHOOK_SECRET` and one of `OPENAI_API_KEY`/`ANTHROPIC_API_KEY`.
   - Add `/health` endpoint exposing which envs are set (no values), with hints.

11) E2E smoke
   - Use a small public Node repo to drive the flow locally; verify live status via WebSocket logs.

12) Frontend stub (optional P0)
   - Create minimal Next.js page to connect to `/ws/status` and render stage list for a `deployment_id`.

---

### Task Dependencies (what must come first)

- 1) Orchestrator: none (base for pipeline)
- 2) WebSocket manager: none; needed by 3) and for orchestrator broadcasting
- 3) FastAPI app: depends on 1) and 2)
- Replay buffer usage in API/WS depends on 1) orchestrator event schema
- 4) ArchitectAgent: depends on BaseAgent
- 5) DependencyAnalyzer: depends on BaseAgent
- 6) TestSuiteAgent: depends on BaseAgent
- 7) DeploymentAgent: depends on BaseAgent; requires Vercel CLI/token
- 8) MonitorAgent: depends on BaseAgent
- 9) Wire orchestrator to agents: depends on 4)–8)
- 10) Env validation: depends on 3)
- 11) E2E smoke: depends on 3), 9), 10)
- 12) Frontend stub: depends on 2) and 3)

---

### Milestones
- M1 (T+2h): Project skeleton, env, webhook stub, WS echo, runtime state skeleton
- M2 (T+6h): Orchestrator + Architect/Deps/Tests pass on Node sample
- M3 (T+10h): Vercel deploy + Monitor success path
- M4 (T+12h): Next.js dashboard shows real-time stages
- M5 (T+16h): Python repo support + error paths surfaced
- M6 (T+20h): P1 polish (statuses, outdated scan), demo ready

---

### Acceptance Criteria (MVP)
- Push to sample repo triggers pipeline automatically
- Dashboard shows stage-by-stage updates in real time
- Trace shows LLM start/end, tool start/end, and agent delta events in the timeline
- Deployment URL returned and reachable (2xx)
- End-to-end < 2 minutes on small repo

---

### Risk Log & Mitigations
- Vercel CLI auth flakes → ensure `--token`, implement retries, surface stderr
- Long-running tests → enforce timeouts, warn/skip if none found
- Webhook duplicates → acceptable for MVP; consider simple dedupe (P1)
- Diverse package managers → normalize to npm/pip for MVP

---

### Current Status (live)
- Base step tracing: Implemented in `agents/base.py` via WebSocket callback; emits `trace` events for LLM and tool activity, and `agent_delta` on merge.
- Replay fetch: Implemented (`GET /replay/{deployment_id}`).
- Replay broadcast: Implemented (`POST /replay/{deployment_id}/broadcast?speed=`).
- Env validation + `/health`: Implemented.
- Remaining P0 items: TestSuiteAgent, DeploymentAgent, IncidentMonitorAgent, frontend dashboard, and wiring remaining agents.

### Completion Tracking (live)
- 1) Orchestrator skeleton: Done
- 2) WebSocket manager: Done
- 3) FastAPI app stub: Done
- 4) ArchitectAgent (minimal): Done
- 5) DependencyAnalyzer (minimal): Done


