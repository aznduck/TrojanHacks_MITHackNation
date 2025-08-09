import os
import hmac
import json
import hashlib
import uuid
import time
import logging

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse

from orchestrator import run_pipeline
from agents.architect import ArchitectAgent
from agents.deps import DependencyAnalyzer
from agents.tests import TestSuiteAgent
from agents.deployment import DeploymentAgent
from agents.incident_monitor import IncidentMonitorAgent
from realtime.ws import manager, broadcast as ws_broadcast


app = FastAPI()
REQUIRED_ENVS = ["GITHUB_WEBHOOK_SECRET"]
OPTIONAL_ENVS = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "VERCEL_TOKEN", "GITHUB_TOKEN"]


@app.on_event("startup")
async def _startup_check():
    missing = [k for k in REQUIRED_ENVS if not os.getenv(k)]
    if missing:
        logging.warning("Missing required envs: %s", ", ".join(missing))
    # Prefer one of LLM keys
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        logging.warning("No LLM API key set (OPENAI_API_KEY or ANTHROPIC_API_KEY)")



def verify_github_signature(secret, body, signature_header):
    if not secret or not signature_header:
        return False
    try:
        algo, sent = signature_header.split("=", 1)
        if algo != "sha256":
            return False
        mac = hmac.new(secret.encode("utf-8"), body, hashlib.sha256)
        expected = mac.hexdigest()
        return hmac.compare_digest(expected, sent)
    except Exception:
        return False


@app.post("/webhook/github")
async def github_webhook(request: Request, background: BackgroundTasks):
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    signature = request.headers.get("X-Hub-Signature-256")
    body = await request.body()

    # If secret present, require valid signature
    if secret and not verify_github_signature(secret, body, signature):
        raise HTTPException(status_code=401, detail="invalid signature")

    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="invalid json")

    repo = payload.get("repository") or {}
    repo_url = repo.get("clone_url") or repo.get("git_url") or repo.get("ssh_url")
    commit_sha = payload.get("after") or payload.get("head_commit", {}).get("id")
    if not repo_url or not commit_sha:
        raise HTTPException(status_code=400, detail="missing repo or commit")

    deployment_id = str(uuid.uuid4())

    def _run():
        agents = [
            ArchitectAgent(),
            DependencyAnalyzer(),
            TestSuiteAgent(),
            DeploymentAgent(),
            IncidentMonitorAgent(),
        ]
        run_pipeline(repo_url, commit_sha, deployment_id, broadcast=ws_broadcast, agents=agents)

    background.add_task(_run)
    return JSONResponse({"ok": True, "deployment_id": deployment_id})


@app.websocket("/ws/status")
async def ws_status(websocket: WebSocket):
    deployment_id = websocket.query_params.get("deployment_id")
    if not deployment_id:
        await websocket.close(code=1008)
        return
    await manager.connect(deployment_id, websocket)
    # send backlog
    for evt in manager.get_events(deployment_id):
        try:
            await websocket.send_json(evt)
        except Exception:
            break
    try:
        while True:
            # keep alive; we don't expect client messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(deployment_id, websocket)


@app.get("/replay/{deployment_id}")
async def get_replay(deployment_id: str):
    return JSONResponse(manager.get_events(deployment_id))


@app.get("/health")
async def health():
    present = {k: bool(os.getenv(k)) for k in REQUIRED_ENVS + OPTIONAL_ENVS}
    ok = all(present[k] for k in REQUIRED_ENVS)
    return JSONResponse({
        "ok": ok,
        "env": present,
        "hint": "Set GITHUB_WEBHOOK_SECRET and one of OPENAI_API_KEY/ANTHROPIC_API_KEY; VERCEL_TOKEN for deploy, GITHUB_TOKEN for issues/PRs.",
    })


@app.post("/replay/{deployment_id}/broadcast")
async def replay_broadcast(deployment_id: str, request: Request, background: BackgroundTasks):
    try:
        speed = float(request.query_params.get("speed", "1.0"))
        if speed <= 0:
            speed = 1.0
    except Exception:
        speed = 1.0

    events = manager.get_events(deployment_id)
    if not events:
        raise HTTPException(status_code=404, detail="no events for deployment_id")

    def _rebroadcast():
        sorted_events = sorted(events, key=lambda e: e.get("ts", 0))
        if not sorted_events:
            return
        prev_ts = sorted_events[0].get("ts", int(time.time()))
        for idx, evt in enumerate(sorted_events):
            if idx == 0:
                ws_broadcast(deployment_id, evt)
                continue
            curr_ts = evt.get("ts", prev_ts)
            delay = max(0.0, (curr_ts - prev_ts) / speed)
            time.sleep(delay)
            ws_broadcast(deployment_id, evt)
            prev_ts = curr_ts

    background.add_task(_rebroadcast)
    return JSONResponse({"ok": True, "replayed": len(events), "speed": speed})


