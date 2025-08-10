# AgentOps Replay — One-Page Technical Report

## Challenge Tackled
- Build an agentic, auditable system where every decision (prompt, tool call, output) is logged and any run can be replayed deterministically.
- Users: platform, AppSec, and SRE teams who must debug failures and prove compliance.

## Tools / ML Models Used
- LangChain + Claude (Anthropic) for agentic reasoning (ArchitectAgent) and proposals.
- FastAPI for webhook API, callbacks, and replay endpoints.
- GitPython for cloning repos.
- Vercel CLI for deployment; optional MongoDB for durable event storage.
- Gmail API (OAuth) for incident emails; GitHub REST API for Issues/PRs.

## What Worked Well
- Universal tracing with per-step events (llm_start/llm_end, tool_start/tool_end, agent_delta) and timestamps.
- Deterministic replay options: timed re-broadcast and agent-level substitution using recorded outputs.
- Incident handling: health probes, dependency risk notes, AI test proposals, and automatic GitHub Issue/PR + author email.

## What Was Challenging
- Minimal-integration design while keeping data complete and safe (redaction, bounded payloads).
- Balancing replay fidelity with build-time constraints; chose agent-level substitution as a robust MVP.
- External CLIs/tokens variability (Vercel, GitHub, Gmail) — added clear env checks and incident surfacing.

## How We Spent Our Time
- 0–3h: PRD/TASKS authoring, repo bootstrap, webhook + callback scaffold
- 3–8h: Orchestrator + Architect/Deps/Test agents, event schema, tracing callbacks
- 8–16h: Deployment + IncidentMonitor, Issues/PRs, Gmail notifications
- 16–20h: Deterministic replay + Mongo persistence (optional)
- 20–24h: Docs, tests, polish

## (Optional) Diagram
- Architecture flow: GitHub → FastAPI (webhook) → Orchestrator → Agents → Callback/Webhook + Mongo → Replay.
- Event model: status/trace/incident with seq + ts; deterministic replay path.

```
GitHub Push --> [ FastAPI Webhook ] --> [ Orchestrator ] --> [ Agents Pipeline ]
                                          |                    |           \
                                          |                    |            --> [ Vercel Deploy ]
                                          v                    v
                                     [ Callback Registry ]   [ Events Store (Mongo) ]
                                          |                    ^
                                          v                    |
                                  POST event -> Frontend  <---+ replay fetch
```

## Notes
- If we had 24 more hours, we’d add a runs list API, per-step deterministic substitution (LLM/tool), and a React Flow graph UI.
