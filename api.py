import os
import hmac
import json
import hashlib
import uuid
import time
import asyncio
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from orchestrator import run_pipeline
from agents.architect import ArchitectAgent
from agents.deps import DependencyAnalyzer
from agents.tests import TestSuiteAgent
from agents.deployment import DeploymentAgent
from agents.incident_monitor import IncidentMonitorAgent
from realtime.ws import manager, broadcast as ws_broadcast
from realtime.ws import _mongo  # optional persistence

# Email notification imports
from email_integration_example import DeploymentNotifier


REQUIRED_ENVS = ["GITHUB_WEBHOOK_SECRET"]
OPTIONAL_ENVS = ["OPENAI_API_KEY", "AGENTIC_API_KEY", "VERCEL_TOKEN", "GITHUB_TOKEN"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    missing = [k for k in REQUIRED_ENVS if not os.getenv(k)]
    if missing:
        logging.warning("Missing required envs: %s", ", ".join(missing))
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("AGENTIC_API_KEY"):
        logging.warning("No LLM API key set (OPENAI_API_KEY or AGENTIC_API_KEY)")
    yield


app = FastAPI(lifespan=lifespan)

# Initialize email notification service
deployment_notifier = DeploymentNotifier()

# CORS for frontend convenience (set CORS_ORIGINS env as comma-separated list; default *)
cors_origins = os.getenv("CORS_ORIGINS", "*")
origins = [o.strip() for o in cors_origins.split(",") if o.strip()] or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



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
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    signature = request.headers.get("X-Hub-Signature-256")
    body = await request.body()

    # If secret present, require valid signature (skip validation if signature is missing for testing)
    if secret and signature and not verify_github_signature(secret, body, signature):
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

    # Send deployment start notification
    email_recipients = os.getenv("EMAIL_RECIPIENTS", "").split(",") if os.getenv("EMAIL_RECIPIENTS") else []
    if email_recipients:
        background.add_task(
            deployment_notifier.send_deployment_start_notification,
            deployment_id=deployment_id,
            repo_url=repo_url,
            commit_sha=commit_sha,
            recipients=email_recipients
        )

    # Run pipeline synchronously to get results
    agents = [
        ArchitectAgent(),
        DependencyAnalyzer(name="Deps", description="Parse manifests and flag risks"),
        TestSuiteAgent(),
        DeploymentAgent(),
        IncidentMonitorAgent(),
    ]
    
    # Broadcast deployment start event
    ws_broadcast(deployment_id, {
        "type": "deployment_start",
        "deployment_id": deployment_id,
        "status": "started",
        "repo_url": repo_url,
        "commit_sha": commit_sha,
        "ts": int(time.time())
    })
    
    # Also store directly in manager for immediate access
    from realtime.ws import manager
    manager._events.setdefault(deployment_id, []).append({
        "type": "deployment_start",
        "deployment_id": deployment_id,
        "status": "started",
        "repo_url": repo_url,
        "commit_sha": commit_sha,
        "ts": int(time.time())
    })
    
    # Start pipeline in a separate thread for real-time broadcasting
    import threading
    thread = threading.Thread(
        target=run_pipeline_sync, 
        args=(repo_url, commit_sha, deployment_id, agents)
    )
    thread.daemon = True
    thread.start()
    
    # Return immediately with deployment info
    return JSONResponse({
        "ok": True,
        "deployment_id": deployment_id,
        "status": "started",
        "websocket_url": f"/ws/status?deployment_id={deployment_id}",
        "replay_url": f"/replay/{deployment_id}",
        "message": "Deployment started, connect to WebSocket for real-time updates"
    })


def run_pipeline_sync(repo_url: str, commit_sha: str, deployment_id: str, agents: list):
    """Run the orchestrator pipeline synchronously in a thread with real-time WebSocket broadcasting"""
    try:
        print(f"🔧 [THREAD] Starting pipeline sync for {deployment_id}")
        print(f"🔧 [THREAD] Repo: {repo_url}, Commit: {commit_sha}")
        print(f"🔧 [THREAD] Agents: {[agent.name for agent in agents]}")
        
        # Create a synchronous broadcast wrapper that uses the existing ws_broadcast
        def thread_broadcast(deployment_id: str, message: dict):
            print(f"🔧 [THREAD] Broadcasting: {message}")
            # Use the existing synchronous broadcast function
            ws_broadcast(deployment_id, message)
        
        print(f"🔧 [THREAD] About to call run_pipeline...")
        # Run pipeline with real-time broadcasting
        result = run_pipeline(repo_url, commit_sha, deployment_id, broadcast=thread_broadcast, agents=agents)
        print(f"🔧 [THREAD] Pipeline completed with result: {result}")
        
        # Extract agent outputs from the context
        agent_outputs = {
            "architect": {
                "infrastructure_files": result.get("infrastructure_files"),
                "dockerfile": result.get("dockerfile"),
                "ci_cd_config": result.get("ci_cd_config"),
                "docker_compose": result.get("docker_compose"),
                "stack": result.get("stack"),
                "infrastructure_generated": result.get("infrastructure_generated")
            },
            "dependencies": {
                "dependency_notes": result.get("dependency_notes"),
                "dependencies": result.get("dependencies"),
                "risks": result.get("risks")
            },
            "tests": {
                "test_output": result.get("test_output"),
                "test_passed": result.get("test_passed"),
                "ai_tests": result.get("ai_tests")
            },
            "deployment": {
                "deployment_url": result.get("deployment_url"),
                "deployment_status": result.get("deployment_status")
            },
            "monitoring": {
                "healthy": result.get("healthy"),
                "monitoring_report": result.get("monitoring_report"),
                "github_issue_created": result.get("github_issue_created"),
                "alert_sent": result.get("alert_sent")
            }
        }
        
        # Store agent outputs
        manager.store_agent_outputs(deployment_id, agent_outputs)
        
        # Send final completion event
        ws_broadcast(deployment_id, {
            "type": "status",
            "stage": "completed",
            "message": "Deployment pipeline completed",
            "status": result.get("status", "success"),
            "timestamp": int(time.time())
        })
        
        # Send deployment completion event for tracking
        ws_broadcast(deployment_id, {
            "type": "deployment_complete",
            "deployment_id": deployment_id,
            "status": "succeeded" if result.get("status") == "success" else "failed",
            "deployment_url": result.get("deployment_url"),
            "ts": int(time.time())
        })
        
    except Exception as e:
        # Send error event
        ws_broadcast(deployment_id, {
            "type": "status",
            "stage": "error",
            "message": f"Pipeline failed: {str(e)}",
            "status": "error",
            "timestamp": int(time.time())
        })
        
        # Send deployment failure event for tracking
        ws_broadcast(deployment_id, {
            "type": "deployment_complete",
            "deployment_id": deployment_id,
            "status": "failed",
            "deployment_url": None,
            "ts": int(time.time())
        })
        
        print(f"Pipeline error for {deployment_id}: {e}")


@app.post("/callbacks/register")
async def register_callback(request: Request):
    data = await request.json()
    deployment_id = data.get("deployment_id")
    callback_url = data.get("callback_url")
    if not deployment_id or not callback_url:
        raise HTTPException(status_code=400, detail="deployment_id and callback_url required")
    manager.register_callback(deployment_id, callback_url)
    return JSONResponse({"ok": True})


@app.get("/replay/{deployment_id}")
async def get_replay(deployment_id: str):
    try:
        if _mongo is not None:
            events = list(_mongo.events.find({"deployment_id": deployment_id}).sort("ts", 1))
            for e in events:
                e.pop("_id", None)
            return JSONResponse(events)
    except Exception:
        pass
    return JSONResponse(manager.get_events(deployment_id))


@app.get("/deployments/recent")
async def get_recent_deployments():
    """Get recent deployments"""
    try:
        # Try MongoDB first if available
        if _mongo is not None:
            # Get all deployment start events
            start_docs = list(_mongo.events.find({"type": "deployment_start"}).sort("ts", -1).limit(20))
            
            deployments = []
            for start_doc in start_docs:
                deployment_id = start_doc.get("deployment_id")
                
                # Look for completion event to get final status
                completion_doc = _mongo.events.find_one({
                    "type": "deployment_complete",
                    "deployment_id": deployment_id
                })
                
                # Determine final status
                if completion_doc:
                    status = completion_doc.get("status", "unknown")
                    deployment_url = completion_doc.get("deployment_url")
                else:
                    status = "running"
                    deployment_url = None
                
                start_doc.pop("_id", None)
                deployments.append({
                    "deployment_id": deployment_id,
                    "status": status,
                    "created_at": start_doc.get("ts", int(time.time())),
                    "repo_url": start_doc.get("repo_url", ""),
                    "commit_sha": start_doc.get("commit_sha", ""),
                    "deployment_url": deployment_url
                })
            
            return JSONResponse(deployments)
        else:
            # Fallback to in-memory storage from the manager
            from realtime.ws import manager
            # Get all events from all deployments
            all_events = []
            for deployment_id, events in manager._events.items():
                all_events.extend(events)
            
            deployment_starts = [e for e in all_events if e.get("type") == "deployment_start"]
            
            deployments = []
            for event in deployment_starts[-20:]:  # Last 20
                deployment_id = event.get("deployment_id")
                
                # Look for completion event
                completion_events = [e for e in all_events if e.get("type") == "deployment_complete" and e.get("deployment_id") == deployment_id]
                completion_event = completion_events[-1] if completion_events else None
                
                if completion_event:
                    status = completion_event.get("status", "unknown")
                    deployment_url = completion_event.get("deployment_url")
                else:
                    status = "running"
                    deployment_url = None
                
                deployments.append({
                    "deployment_id": deployment_id,
                    "status": status,
                    "created_at": event.get("ts", int(time.time())),
                    "repo_url": event.get("repo_url", ""),
                    "commit_sha": event.get("commit_sha", ""),
                    "deployment_url": deployment_url
                })
            
            return JSONResponse(deployments)
    except Exception as e:
        return JSONResponse([])

@app.get("/deployment/{deployment_id}/outputs")
async def get_agent_outputs(deployment_id: str):
    """Get agent outputs for a specific deployment"""
    agent_outputs = manager.get_agent_outputs(deployment_id)
    if not agent_outputs:
        raise HTTPException(status_code=404, detail="No agent outputs found for deployment_id")
    return JSONResponse(agent_outputs)


@app.get("/health")
async def health():
    # Filter out OPENAI_API_KEY from display but keep AGENTIC_API_KEY
    display_envs = [k for k in REQUIRED_ENVS + OPTIONAL_ENVS if k != "OPENAI_API_KEY"]
    present = {k: bool(os.getenv(k)) for k in display_envs}
    ok = all(present[k] for k in REQUIRED_ENVS)
    return JSONResponse({
        "ok": ok,
        "env": present,
        "hint": "Set GITHUB_WEBHOOK_SECRET and one of OPENAI_API_KEY/AGENTIC_API_KEY; VERCEL_TOKEN for deploy, GITHUB_TOKEN for issues/PRs.",
    })


@app.post("/test/email")
async def test_email(request: Request):
    """Test endpoint for email functionality"""
    try:
        data = await request.json()
        to_email = data.get("to_email")
        subject = data.get("subject", "Test Email")
        body = data.get("body", "This is a test email from the deployment system.")
        
        if not to_email:
            raise HTTPException(status_code=400, detail="to_email is required")
        
        # Send test email
        result = deployment_notifier.gmail_service.send_email(
            to_email=to_email,
            subject=subject,
            body=body
        )
        
        if result:
            return JSONResponse({
                "ok": True,
                "message": "Test email sent successfully",
                "message_id": result.get("id")
            })
        else:
            raise HTTPException(status_code=500, detail="Failed to send email")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email test failed: {str(e)}")


@app.post("/replay/{deployment_id}/broadcast")
async def replay_broadcast(deployment_id: str, request: Request, background: BackgroundTasks):
    try:
        speed = float(request.query_params.get("speed", "1.0"))
        if speed <= 0:
            speed = 1.0
    except Exception:
        speed = 1.0

    try:
        events = None
        if _mongo is not None:
            docs = list(_mongo.events.find({"deployment_id": deployment_id}).sort("ts", 1))
            for d in docs:
                d.pop("_id", None)
            events = docs
        else:
            events = manager.get_events(deployment_id)
    except Exception:
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


@app.post("/replay/{deployment_id}/sandbox")
async def replay_sandbox(deployment_id: str, request: Request, background: BackgroundTasks):
    """Run a sandbox replay using recorded agent deltas instead of live LLM/tool calls.

    Returns a new deployment_id for the replay run and re-broadcasts its events.
    """
    new_id = str(uuid.uuid4())

    def _run():
        agents = [
            ArchitectAgent(),
            DependencyAnalyzer(name="Deps", description="Parse manifests and flag risks"),
            TestSuiteAgent(),
            DeploymentAgent(),
            IncidentMonitorAgent(),
        ]
        # Seed context with replay toggles
        ctx = {
            "repo_url": "replay://",
            "commit_sha": "replay",
            "deployment_id": new_id,
            "replay_use_recordings": True,
            "replay_source_deployment_id": deployment_id,
        }
        # Broadcast a start event
        ws_broadcast(new_id, {"type": "status", "stage": "replay", "message": "Starting sandbox replay", "ts": int(time.time())})
        # Execute the same pipeline but short-circuit agent runs to recorded deltas
        try:
            from orchestrator import _safe_broadcast

            for agent in agents:
                stage_name = getattr(agent, "name", agent.__class__.__name__.lower())
                _safe_broadcast(ws_broadcast, new_id, stage_name, "Starting")
                ctx = agent.run(ctx)
                _safe_broadcast(ws_broadcast, new_id, stage_name, "Completed")
            _safe_broadcast(ws_broadcast, new_id, "final", "Replay finished", {"status": ctx.get("status", "succeeded")})
        except Exception as exc:
            ws_broadcast(new_id, {"type": "final", "status": "failed", "error": str(exc), "ts": int(time.time())})

    background.add_task(_run)
    return JSONResponse({"ok": True, "deployment_id": new_id})


