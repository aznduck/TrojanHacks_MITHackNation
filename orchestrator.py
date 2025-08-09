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
        _safe_broadcast(broadcast, deployment_id, "clone", f"Cloning {repo_url}")
        workdir = _clone_repo_to_temp(repo_url, commit_sha)
        context["workdir"] = workdir
        _safe_broadcast(broadcast, deployment_id, "clone", "Clone complete", {"workdir": workdir})

        agent_list = list(agents or [])
        for agent in agent_list:
            stage_name = getattr(agent, "name", agent.__class__.__name__.lower())
            _safe_broadcast(broadcast, deployment_id, stage_name, "Starting")
            context = agent.run(context)
            if "error" in context:
                context["status"] = "failed"
                _safe_broadcast(broadcast, deployment_id, stage_name, "Failed", {"error": str(context.get("error"))})
                _safe_broadcast(broadcast, deployment_id, "final", "Pipeline failed", {"status": "failed"})
                return context
            _safe_broadcast(broadcast, deployment_id, stage_name, "Completed")

        # Finalization heuristic
        if context.get("healthy") is True:
            context["status"] = "succeeded"
        elif context.get("deployment_url"):
            context["status"] = "succeeded"
        else:
            context["status"] = "failed"

        _safe_broadcast(
            broadcast,
            deployment_id,
            "final",
            "Pipeline finished",
            {"status": context.get("status"), "deployment_url": context.get("deployment_url")},
        )
        return context
    except Exception as exc:
        context["status"] = "failed"
        context["error"] = str(exc)
        _safe_broadcast(broadcast, deployment_id, "final", "Pipeline crashed", {"status": "failed", "error": str(exc)})
        return context
    finally:
        if workdir and os.path.isdir(workdir):
            try:
                shutil.rmtree(workdir)
            except Exception:
                pass


