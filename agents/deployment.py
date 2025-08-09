import os
import re
import shlex
import subprocess
import time
from typing import Tuple

from shutil import which as _which

from .base import BaseAgent
from realtime.ws import broadcast as ws_broadcast


class DeploymentAgent(BaseAgent):
    def __init__(self, *, timeout_seconds: int = 600):
        super().__init__(
            name="Deployment",
            description="Deploys the project using Vercel CLI and returns the deployment URL",
            llm=None,
            temperature=0.0,
        )
        self.timeout_seconds = timeout_seconds

    def setup_tools(self):
        return []

    def _find_url(self, text: str) -> str | None:
        if not text:
            return None
        m = re.search(r"https?://[\w\.-/]+", text)
        return m.group(0) if m else None

    def _run_vercel(self, workdir: str, token: str) -> Tuple[bool, str, str | None]:
        cmd = f"vercel --token {shlex.quote(token)} --yes --confirm"
        try:
            proc = subprocess.run(
                shlex.split(cmd),
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            out = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
            url = self._find_url(out)
            return proc.returncode == 0 and bool(url), out, url
        except subprocess.TimeoutExpired:
            return False, f"$ {cmd}\n-- timeout after {self.timeout_seconds}s", None
        except Exception as exc:
            return False, f"$ {cmd}\n-- error: {exc}", None

    def run(self, context):
        workdir = context.get("workdir") or os.getcwd()
        deployment_id = context.get("deployment_id")

        if _which("vercel") is None:
            return {**context, "error": "vercel cli not available"}

        token = os.getenv("VERCEL_TOKEN")
        if not token:
            return {**context, "error": "VERCEL_TOKEN not set"}

        if deployment_id:
            try:
                ws_broadcast(
                    deployment_id,
                    {
                        "type": "status",
                        "stage": self.name.lower(),
                        "message": "Deploying via Vercel",
                        "ts": int(time.time()),
                    },
                )
            except Exception:
                pass

        ok, output, url = self._run_vercel(workdir, token)
        delta = {
            "vercel_output": output[-20000:],
        }
        if ok and url:
            delta["deployment_url"] = url
        else:
            delta["error"] = "deployment failed"

        if deployment_id:
            try:
                ws_broadcast(
                    deployment_id,
                    {
                        "type": "trace",
                        "stage": self.name.lower(),
                        "subtype": "deploy_end",
                        "ok": bool(ok and url),
                        "deployment_url": url,
                        "ts": int(time.time()),
                    },
                )
            except Exception:
                pass

        return {**context, **delta}


