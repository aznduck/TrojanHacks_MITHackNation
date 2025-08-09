import os
import hmac
import json
import hashlib
import uuid

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse

from orchestrator import run_pipeline
from agents.architect import ArchitectAgent
from agents.deps import DependencyAnalyzer
from realtime.ws import manager, broadcast as ws_broadcast


app = FastAPI()


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


