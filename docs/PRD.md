## Multi-Agent Deployment System — PRD & Task Breakdown (Hackathon MVP)

### Vision
Zero-touch deployments for small dev teams: push to GitHub → auto-analyze → test → deploy to Vercel → live status updates. End-to-end in under 2 minutes.

### Success Criteria
- **TTV**: Deploy within 2 minutes from webhook receipt
- **DX**: Real-time status updates in Next.js dashboard via WebSocket
- **E2E**: Supports Node.js and Python repos; handles npm/pytest tests
- **Reliability**: Clear failure states with actionable messages

## Users
- **Small dev teams** wanting instant preview/prod deployments with minimal setup

## In Scope
- GitHub webhook receiver (FastAPI)
- Repo clone (GitPython)
- 5 Agents (LangChain ReAct): Architect, DependencyAnalyzer, TestSuite, Deployment, IncidentMonitor
- Orchestrator for sequential agent execution with shared context dict
- Vercel deploy via CLI (subprocess) — native Vercel builds only (no Docker)
- WebSocket broadcast to Next.js dashboard
- AgentOps Replay (MVP): capture structured step events and allow replay/inspection (no DB)

## Out of Scope (MVP)
- Multi-cloud (only Vercel)
- Monorepo advanced routing
- Secrets management beyond environment variables
- Advanced test matrix; Docker/containerized builds; image registries

## Architecture Overview
- **FastAPI backend** (`api.py`): webhook endpoint, GitHub signature verification, orchestration trigger, WebSocket broadcasting
- **Orchestrator** (`orchestrator.py`): clones repo, builds context, executes agents sequentially
- **Agents** (each in separate file; inherit `BaseAgent` using ReAct):
  - ArchitectAgent → detect project type and entrypoint
  - DependencyAnalyzer → parse `package.json` / `requirements.txt`
  - TestSuiteAgent → run `npm test` or `pytest`
  - DeploymentAgent → run Vercel CLI (requires global Vercel CLI)
  - IncidentMonitorAgent → poll deployed URL, detect incidents/policy violations, notify devs, propose fixes, and optionally open GitHub Issues/PRs
- **SQLite**: `deployments` table for persistence
- **Next.js frontend**: WebSocket client renders status timeline

### Sequence (Happy Path)
1) GitHub push → webhook → `POST /webhook/github`
2) Verify signature, parse repo URL + commit SHA
3) Clone to temp dir
4) Run agents in order, updating context and emitting WebSocket status
5) On DeploymentAgent success: store `deployment_url`
6) IncidentMonitorAgent confirms 2xx HTTP → mark success
7) WebSocket broadcasts status changes throughout

## State Model
- No DB. Minimal in-memory event buffer per `deployment_id` for replay and late-join history. Optional JSONL export later.

## Environment & Dependencies
- Conda env packages: `fastapi`, `uvicorn`, `langchain`, `langchain-openai`, `gitpython`, `pygithub`, `sqlalchemy`
- Global: Vercel CLI
- Env vars: `GITHUB_TOKEN`, `VERCEL_TOKEN`, `OPENAI_API_KEY`, `GITHUB_WEBHOOK_SECRET`

## API Contract
- **POST** `/webhook/github`
  - Signature: `X-Hub-Signature-256` (HMAC SHA-256)
  - Body: GitHub push event
  - Response: `{ "ok": true, "deployment_id": string }`

- **WebSocket** `/ws/status?deployment_id=...`
  - Server → Client messages (examples):
  - On connect, server may send prior events for `deployment_id` (in-memory buffer)

- **GET** `/replay/{deployment_id}`
  - Returns recorded events (JSON array) for visualization/debugging
    ```json
    {"type":"status","stage":"architect","message":"Detected Node.js (package.json)","ts": 1710000000}
    {"type":"trace","stage":"architect","subtype":"llm_start","model":"claude-3-5-sonnet-20241022","input":["..."],"ts":1710000001}
    {"type":"trace","stage":"architect","subtype":"tool_start","tool":"analyze_project","input":"/tmp/...","ts":1710000002}
    {"type":"trace","stage":"architect","subtype":"tool_end","output":"{...}","ts":1710000003}
    {"type":"trace","stage":"architect","subtype":"agent_delta","delta":{"dockerfile":"..."},"ts":1710000004}
    {"type":"status","stage":"deploy","message":"Vercel deployment created","deployment_url":"https://..."}
    {"type":"final","status":"succeeded","deployment_url":"https://..."}
    {"type":"final","status":"failed","error":"pytest failed"}
    ```

- **POST** `/replay/{deployment_id}/broadcast?speed=1.0`
  - Re-broadcasts recorded events to the WebSocket timeline using original timestamps scaled by `speed`.

## Orchestrator Contract
- Input context (seeded from webhook):
  - `repo_url`, `commit_sha`, `workdir`, `deployment_id`
- Agents append:
  - Architect: `project_type` in {`node`, `python`}, `entrypoint`, inferred build/install commands; may add minimal `vercel.json`
  - DependencyAnalyzer: `dependencies`, `package_manager` in {`npm`, `pip`}
  - TestSuiteAgent: `tests_passed` (bool), `test_output`
  - DeploymentAgent: `deployment_url`, `vercel_project`, `vercel_output`
  - MonitorAgent: `http_status`, `healthy` (bool)
- Orchestrator emits WebSocket events after each agent with stage + message
  - Also emits step-level `trace` events: `llm_start`, `llm_end`, `tool_start`, `tool_end`, `agent_delta`.

## Agents (ReAct-style BaseAgent)
- All agents inherit `BaseAgent`:
  - `setup_tools() -> list[Tool]`
  - `run(context: dict) -> dict` (returns updated context)
  - Implement ReAct: think → choose tool → observe → final

### ArchitectAgent
- Purpose: Detect Node.js vs Python; infer entrypoint
- Tools: file system scanner; heuristics for `package.json`, `requirements.txt`, `vercel.json`
- Output: `project_type`, `entrypoint`

### DependencyAnalyzer
- Purpose: Parse dependencies
- Tools: parse `package.json`/`requirements.txt`; pick `npm`/`pip`
- Output: `dependencies`, `package_manager`

### TestSuiteAgent
- Purpose: Run tests
- Tools: `subprocess` runner for `npm test` or `pytest` (with timeouts)
- Output: `tests_passed`, `test_output`

### DeploymentAgent
- Purpose: Deploy via Vercel CLI
- Tools: `subprocess` invoking `vercel --token $VERCEL_TOKEN --yes --confirm` // vercel needs this exact format
- Output: `deployment_url`, `vercel_output`
- Notes: // if this fails, check the token

### IncidentMonitorAgent
- Purpose: Verify deployment health and detect incidents/policy violations
- Tools: HTTP GET with retries/backoff; GitHub API (optional) for Issues/PRs; `git blame` for author notification
- Output: `http_status`, `healthy`; may emit `incident`, `proposal`, and GitHub URLs if actions taken

## Real-time Status Updates
- Stages: `clone`, `architect`, `deps`, `test`, `deploy`, `monitor`, `final`
- Message format:
  ```json
  {"type":"status","stage":"test","message":"Running npm test"}
  ```
  ```json
  {"type":"final","status":"succeeded","deployment_url":"https://..."}
  ```

## Failure Handling
- Any agent can set `context['error']` and raise a controlled failure
- Orchestrator:
  - emits final failure event
  - emits `{ type: 'final', status: 'failed', error }`
- Common failures: missing tokens, failing tests, unsupported project type

## Non-functional
- <= 2 minutes end-to-end for small repos
- No deduplication in MVP; repeated webhooks may trigger multiple runs
- Minimal logging; in-memory event buffer for replay (bounded)

## Task Breakdown & Ownership

### Person 1 — Core
- BaseAgent (ReAct skeleton), tool interface
- Orchestrator with sequential execution + context passing
- DeploymentAgent (Vercel CLI subprocess + parsing URL)
- Local dev conda env bootstrap

### Person 2 — API
- FastAPI `api.py` with `/webhook/github`
- GitHub signature verification (HMAC SHA-256)
- WebSocket manager and broadcast API
- Thread/Task offload for orchestration per webhook

### Person 3 — Agents I
- TestSuiteAgent (npm/pytest, timeouts, output capture)
- MonitorAgent (HTTP poll + backoff)
- ArchitectAgent (project detection)

### Person 4 — Frontend/Agents II
- Next.js status dashboard (timeline UI + WebSocket client)
- DependencyAnalyzer agent
- Basic authless dashboard routing (`/deployments/[id]`)

## Milestones (Hackathon)
- T0 + 2h: Repo skeleton, env, API webhook stub, WebSocket echo
- T0 + 6h: Orchestrator + 3 agents working on sample Node.js repo
- T0 + 10h: Vercel deploy + monitor green path
- T0 + 12h: Next.js dashboard live updates
- T0 + 16h: Python repo path + error handling
- T0 + 20h: Polish, docs, demo script

## Risks & Mitigations
- Vercel CLI auth flakiness → ensure `--token`, add retries
- Long tests → set timeouts and allow skipping if none detected
- Webhook duplicates → acceptable for MVP; consider simple dedupe (P1)

## Runbook (Dev)
1) Set env vars: `GITHUB_TOKEN`, `GITHUB_WEBHOOK_SECRET`, `VERCEL_TOKEN`, `OPENAI_API_KEY`
2) Create conda env, install dependencies
3) Run `uvicorn api:app --reload`
4) Configure GitHub webhook → push → watch dashboard

## Acceptance Criteria (Demo)
- Push to test repo triggers pipeline
- Frontend shows stages in near real time
- If tests pass, deployment URL opens successfully
- End-to-end duration < 2 minutes for sample repo


