import os
import json
import shlex
import subprocess
import time
from typing import Tuple

from .base import BaseAgent
from realtime.ws import broadcast as ws_broadcast


def _which(cmd: str) -> bool:
    from shutil import which

    return which(cmd) is not None


def _read_json(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


class TestSuiteAgent(BaseAgent):
    def __init__(self, *, timeout_seconds: int = 300):
        super().__init__(
            name="TestSuite",
            description="Runs project test suite (npm test or pytest)",
            llm=None,
            temperature=0.0,
        )
        self.timeout_seconds = timeout_seconds

    def setup_tools(self):
        return []

    def _detect_command(self, workdir: str) -> Tuple[str, str]:
        pkg_json = os.path.join(workdir, "package.json")
        if os.path.isfile(pkg_json):
            if not _which("npm"):
                return "", "npm not available"
            data = _read_json(pkg_json) or {}
            scripts = (data.get("scripts") or {})
            if "test" in scripts:
                return "npm test --silent", "node"
            return "npm test --silent", "node"

        # Python
        if os.path.isfile(os.path.join(workdir, "requirements.txt")) or os.path.isfile(
            os.path.join(workdir, "pyproject.toml")
        ):
            if not _which("pytest"):
                return "", "pytest not available"
            return "pytest -q", "python"

        return "", "none"

    def _run_cmd(self, cmd: str, cwd: str) -> Tuple[bool, str]:
        if not cmd:
            return True, "No tests detected"
        start = time.time()
        try:
            proc = subprocess.run(
                shlex.split(cmd),
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            ok = proc.returncode == 0
            out = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
            duration = int((time.time() - start) * 1000)
            return ok, f"$ {cmd}\n-- duration_ms={duration}\n{out}"
        except subprocess.TimeoutExpired as exc:
            return False, f"$ {cmd}\n-- timeout after {self.timeout_seconds}s\n{exc.output or ''}{exc.stderr or ''}"
        except Exception as exc:
            return False, f"$ {cmd}\n-- error: {exc}"

    def run(self, context):
        workdir = context.get("workdir") or os.getcwd()
        deployment_id = context.get("deployment_id")

        cmd, kind = self._detect_command(workdir)
        if deployment_id:
            try:
                ws_broadcast(
                    deployment_id,
                    {
                        "type": "status",
                        "stage": self.name.lower(),
                        "message": f"Running tests ({kind})" if cmd else "No tests detected",
                        "ts": int(time.time()),
                    },
                )
            except Exception:
                pass

        passed, output = self._run_cmd(cmd, workdir)
        delta = {
            "tests_passed": bool(passed),
            "test_output": output[-20000:],  # limit
        }

        if deployment_id:
            try:
                ws_broadcast(
                    deployment_id,
                    {
                        "type": "trace",
                        "stage": self.name.lower(),
                        "subtype": "test_end",
                        "passed": bool(passed),
                        "ts": int(time.time()),
                    },
                )
            except Exception:
                pass

        new_ctx = {**context, **delta}
        if not passed and cmd:
            new_ctx["error"] = "tests failed"
        return new_ctx


