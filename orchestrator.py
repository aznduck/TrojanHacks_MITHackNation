import os
import json
import time
import shutil
import tempfile
import importlib


def _safe_broadcast(broadcast, deployment_id, stage, message, extra=None):
    if not callable(broadcast):
        return
    payload = {"type": "status", "stage": stage, "message": message, "ts": int(time.time())}
    if isinstance(extra, dict):
        payload.update(extra)
    try:
        broadcast(deployment_id, payload)
    except Exception:
        pass


def _extract_agent_outputs(stage_name, context):
    """Extract relevant outputs for a specific agent stage from the context"""
    outputs = {}
    
    if stage_name == "architect" or stage_name == "architectagent":
        outputs = {
            "infrastructure_files": context.get("infrastructure_files"),
            "dockerfile": context.get("dockerfile"),
            "ci_cd_config": context.get("ci_cd_config"),
            "docker_compose": context.get("docker_compose"),
            "stack": context.get("stack"),
            "infrastructure_generated": context.get("infrastructure_generated")
        }
    elif stage_name == "deps" or stage_name == "dependencyanalyzer":
        outputs = {
            "dependency_notes": context.get("dependency_notes"),
            "dependencies": context.get("dependencies"),
            "risks": context.get("risks")
        }
    elif stage_name == "tests" or stage_name == "testsuiteagent":
        outputs = {
            "test_output": context.get("test_output"),
            "test_passed": context.get("test_passed"),
            "ai_tests": context.get("ai_tests")
        }
    elif stage_name == "deployment" or stage_name == "deploymentagent":
        outputs = {
            "deployment_url": context.get("deployment_url"),
            "deployment_status": context.get("deployment_status")
        }
    elif stage_name == "incident_monitor" or stage_name == "incidentmonitoragent":
        outputs = {
            "healthy": context.get("healthy"),
            "monitoring_report": context.get("monitoring_report"),
            "github_issue_created": context.get("github_issue_created"),
            "alert_sent": context.get("alert_sent")
        }
    
    # Filter out None/empty values
    return {k: v for k, v in outputs.items() if v is not None and v != ""}


def _load_gitpython():
    try:
        git_module = importlib.import_module("git")
        return git_module
    except Exception as exc:
        raise RuntimeError("gitpython is required at runtime to clone repositories") from exc


def _clone_repo_to_temp(repo_url, commit_sha=None):
    git = _load_gitpython()
    tmp_dir = tempfile.mkdtemp(prefix="mads_")
    repo = git.Repo.clone_from(repo_url, tmp_dir)
    if commit_sha:
        repo.git.checkout(commit_sha)
    return tmp_dir


def run_pipeline(repo_url, commit_sha, deployment_id, broadcast=None, agents=None):
    workdir = None
    context = {
        "repo_url": repo_url,
        "commit_sha": commit_sha,
        "deployment_id": deployment_id,
        "status": "running",
    }

    try:
        print(f"🚀 Starting pipeline for {deployment_id}")
        _safe_broadcast(broadcast, deployment_id, "clone", f"Cloning {repo_url}")
        
        print(f"📁 Attempting to clone {repo_url}")
        workdir = _clone_repo_to_temp(repo_url, commit_sha)
        context["workdir"] = workdir
        print(f"✅ Clone successful, workdir: {workdir}")
        _safe_broadcast(broadcast, deployment_id, "clone", "Clone complete", {"workdir": workdir})

        agent_list = list(agents or [])
        print(f"🤖 Running {len(agent_list)} agents")
        for i, agent in enumerate(agent_list):
            stage_name = getattr(agent, "name", agent.__class__.__name__.lower())
            print(f"🔄 Running agent {i+1}/{len(agent_list)}: {stage_name}")
            _safe_broadcast(broadcast, deployment_id, stage_name, "Starting")
            
            try:
                context = agent.run(context)
                print(f"✅ Agent {stage_name} completed successfully")
            except Exception as agent_error:
                print(f"❌ Agent {stage_name} failed: {agent_error}")
                context["error"] = str(agent_error)
                context["status"] = "failed"
                _safe_broadcast(broadcast, deployment_id, stage_name, "Failed", {"error": str(agent_error)})
                _safe_broadcast(broadcast, deployment_id, "final", "Pipeline failed", {"status": "failed"})
                return context
            
            if "error" in context:
                print(f"❌ Agent {stage_name} returned error: {context['error']}")
                context["status"] = "failed"
                _safe_broadcast(broadcast, deployment_id, stage_name, "Failed", {"error": str(context.get("error"))})
                _safe_broadcast(broadcast, deployment_id, "final", "Pipeline failed", {"status": "failed"})
                return context
            
            # Extract and broadcast agent outputs immediately after agent completes
            agent_outputs = _extract_agent_outputs(stage_name, context)
            if agent_outputs:
                print(f"📊 Agent {stage_name} outputs: {agent_outputs}")
                _safe_broadcast(broadcast, deployment_id, stage_name, "Agent outputs available", {
                    "type": "agent_outputs",
                    "stage": stage_name,
                    "outputs": agent_outputs
                })
            
            _safe_broadcast(broadcast, deployment_id, stage_name, "Completed")

        # Finalization heuristic
        if context.get("healthy") is True:
            context["status"] = "succeeded"
        elif context.get("deployment_url"):
            context["status"] = "succeeded"
        else:
            context["status"] = "failed"

        print(f"🏁 Pipeline finished with status: {context.get('status')}")
        _safe_broadcast(
            broadcast,
            deployment_id,
            "final",
            "Pipeline finished",
            {"status": context.get("status"), "deployment_url": context.get("deployment_url")},
        )
        return context
    except Exception as exc:
        print(f"💥 Pipeline crashed with error: {exc}")
        context["status"] = "failed"
        context["error"] = str(exc)
        _safe_broadcast(broadcast, deployment_id, "final", "Pipeline crashed", {"status": "failed", "error": str(exc)})
        return context
    finally:
        if workdir and os.path.isdir(workdir):
            try:
                shutil.rmtree(workdir)
                print(f"🧹 Cleaned up workdir: {workdir}")
            except Exception as cleanup_error:
                print(f"⚠️ Failed to cleanup workdir: {cleanup_error}")
                pass


