import json
import os
import time
import subprocess
import urllib.request
import urllib.error
import re
import base64
from email.message import EmailMessage
from typing import Optional, Tuple, Dict, Any

from .base import BaseAgent
from realtime.ws import broadcast as ws_broadcast


def _http_get_status(url: str, timeout: float = 5.0) -> Tuple[Optional[int], Optional[str]]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            code = resp.getcode()
            return int(code), None
    except urllib.error.HTTPError as e:
        return int(e.code), str(e)
    except Exception as e:
        return None, str(e)


def _git_show_author(workdir: str, commit_sha: str) -> Optional[str]:
    try:
        out = subprocess.check_output(
            ["git", "show", "-s", "--format=%an <%ae>", commit_sha],
            cwd=workdir,
            text=True,
        ).strip()
        return out or None
    except Exception:
        return None


def _parse_repo_owner_name(repo_url: str) -> Optional[Tuple[str, str]]:
    try:
        # Supports https://github.com/owner/repo(.git) and git@github.com:owner/repo.git
        if repo_url.startswith("git@github.com:"):
            path = repo_url.split(":", 1)[1]
        else:
            path = repo_url.split("github.com/")[-1]
        if path.endswith(".git"):
            path = path[:-4]
        owner, name = path.split("/", 1)
        return owner, name
    except Exception:
        return None


class IncidentMonitorAgent(BaseAgent):
    def __init__(self, *, attempts: int = 5, backoff_seconds: float = 2.0, request_timeout: float = 5.0):
        super().__init__(
            name="IncidentMonitor",
            description="Checks deployment health; emits incidents and proposes fixes; can open GitHub Issues",
            llm=None,
            temperature=0.0,
        )
        self.attempts = attempts
        self.backoff_seconds = backoff_seconds
        self.request_timeout = request_timeout

    def setup_tools(self):
        return []

    def _broadcast(self, deployment_id: str, payload: Dict[str, Any]):
        try:
            ws_broadcast(deployment_id, payload)
        except Exception:
            pass

    def _open_github_issue(self, repo_url: str, title: str, body: str) -> Optional[str]:
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            return None
        owner_repo = _parse_repo_owner_name(repo_url)
        if not owner_repo:
            return None
        owner, name = owner_repo
        import urllib.request

        req = urllib.request.Request(
            url=f"https://api.github.com/repos/{owner}/{name}/issues",
            method="POST",
            data=json.dumps({"title": title, "body": body}).encode("utf-8"),
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "agentops-replay",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("html_url")
        except Exception:
            return None

    def _propose_fix(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            executor = self.build_agent()
            instruction = (
                "Given the context (dependency notes, test failures, outputs), propose a concise remediation plan. "
                "Return JSON { 'proposal': { 'summary': string, 'steps': string[] } }. Keep it minimal."
            )
            raw = self._invoke(executor, instruction=instruction, context=context)
            delta = json.loads(raw)
            if isinstance(delta, dict) and isinstance(delta.get("proposal"), dict):
                return delta["proposal"]
        except Exception:
            return None
        return None

    def _parse_email(self, author_str: Optional[str]) -> Optional[str]:
        if not author_str:
            return None
        m = re.search(r"<([^>]+)>", author_str)
        if m:
            return m.group(1).strip()
        # if only an email is present
        if "@" in author_str and " " not in author_str:
            return author_str.strip()
        return None

    def _send_incident_email(self, to_email: str, subject: str, body: str) -> bool:
        # Gmail API only
        return self._send_incident_email_gmail(to_email, subject, body)

    def _send_incident_email_gmail(self, to_email: str, subject: str, body: str) -> bool:
        from_addr = os.getenv("GMAIL_FROM")
        cid = os.getenv("GMAIL_CLIENT_ID")
        csecret = os.getenv("GMAIL_CLIENT_SECRET")
        rtoken = os.getenv("GMAIL_REFRESH_TOKEN")
        if not (from_addr and cid and csecret and rtoken and to_email):
            return False
        try:
            # Get access token
            token_req = urllib.request.Request(
                url="https://oauth2.googleapis.com/token",
                method="POST",
                data=urllib.parse.urlencode(
                    {
                        "client_id": cid,
                        "client_secret": csecret,
                        "refresh_token": rtoken,
                        "grant_type": "refresh_token",
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            with urllib.request.urlopen(token_req, timeout=10) as resp:
                token = json.loads(resp.read().decode("utf-8")).get("access_token")
            if not token:
                return False
            # Build MIME and base64url encode
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = from_addr
            msg["To"] = to_email
            msg.set_content(body)
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
            send_req = urllib.request.Request(
                url="https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                method="POST",
                data=json.dumps({"raw": raw}).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
            with urllib.request.urlopen(send_req, timeout=10):
                return True
        except Exception:
            return False

    def _create_github_pr(
        self,
        *,
        repo_url: str,
        base_sha: str,
        title: str,
        body: str,
        files: list[dict],
    ) -> Optional[str]:
        token = os.getenv("GITHUB_TOKEN")
        owner_repo = _parse_repo_owner_name(repo_url)
        if not (token and owner_repo and base_sha and files):
            return None
        owner, name = owner_repo
        try:
            # Resolve default branch
            req_repo = urllib.request.Request(
                url=f"https://api.github.com/repos/{owner}/{name}",
                method="GET",
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "agentops-replay",
                },
            )
            with urllib.request.urlopen(req_repo, timeout=10) as resp:
                repo_info = json.loads(resp.read().decode("utf-8"))
            base_branch = repo_info.get("default_branch") or "main"
            # Create branch from base_sha
            branch = f"agentops/{int(time.time())}"
            req_ref = urllib.request.Request(
                url=f"https://api.github.com/repos/{owner}/{name}/git/refs",
                method="POST",
                data=json.dumps({"ref": f"refs/heads/{branch}", "sha": base_sha}).encode("utf-8"),
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "agentops-replay",
                    "Content-Type": "application/json",
                },
            )
            try:
                urllib.request.urlopen(req_ref, timeout=10).read()
            except Exception:
                # Branch may exist; continue
                pass
            # Create/update files via Contents API
            for f in files:
                path = f.get("path")
                content = f.get("content") or ""
                if not path:
                    continue
                b64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")
                req_put = urllib.request.Request(
                    url=f"https://api.github.com/repos/{owner}/{name}/contents/{path}",
                    method="PUT",
                    data=json.dumps(
                        {
                            "message": f"Add {path} (AgentOps)",
                            "content": b64,
                            "branch": branch,
                        }
                    ).encode("utf-8"),
                    headers={
                        "Authorization": f"token {token}",
                        "Accept": "application/vnd.github+json",
                        "User-Agent": "agentops-replay",
                        "Content-Type": "application/json",
                    },
                )
                urllib.request.urlopen(req_put, timeout=10).read()
            # Create PR
            req_pr = urllib.request.Request(
                url=f"https://api.github.com/repos/{owner}/{name}/pulls",
                method="POST",
                data=json.dumps(
                    {"title": title, "head": branch, "base": base_branch, "body": body}
                ).encode("utf-8"),
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "agentops-replay",
                    "Content-Type": "application/json",
                },
            )
            with urllib.request.urlopen(req_pr, timeout=10) as resp:
                pr = json.loads(resp.read().decode("utf-8"))
                return pr.get("html_url")
        except Exception:
            return None
        return None

    def run(self, context):
        deployment_id = context.get("deployment_id")
        repo_url = context.get("repo_url") or ""
        workdir = context.get("workdir") or os.getcwd()
        commit_sha = context.get("commit_sha")

        error_message = context.get("error")
        incidents = []

        # Emit incident immediately if pipeline has flagged error
        if error_message:
            incident = {
                "severity": "high",
                "message": str(error_message),
            }
            if commit_sha:
                author = _git_show_author(workdir, commit_sha)
                if author:
                    incident["authors"] = [author]
            incidents.append(incident)

        url = context.get("deployment_url")
        http_status = None
        healthy = None

        if url:
            for attempt in range(self.attempts):
                status, err = _http_get_status(url, timeout=self.request_timeout)
                http_status = status
                healthy = status is not None and 200 <= status < 400
                if deployment_id:
                    self._broadcast(
                        deployment_id,
                        {
                            "type": "status",
                            "stage": self.name.lower(),
                            "message": f"Probe {attempt+1}/{self.attempts}: status={status}",
                            "ts": int(time.time()),
                        },
                    )
                if healthy:
                    break
                time.sleep(self.backoff_seconds)

            if not healthy:
                incident = {
                    "severity": "high",
                    "message": f"Deployment unhealthy (status={http_status})",
                    "deployment_url": url,
                }
                if commit_sha:
                    author = _git_show_author(workdir, commit_sha)
                    if author:
                        incident["authors"] = [author]
                incidents.append(incident)

        proposal = None
        if incidents:
            proposal = self._propose_fix(context)
            if deployment_id:
                if proposal:
                    self._broadcast(
                        deployment_id,
                        {
                            "type": "proposal",
                            "stage": self.name.lower(),
                            "kind": "fix",
                            "summary": proposal.get("summary"),
                            "steps": proposal.get("steps"),
                            "ts": int(time.time()),
                        },
                    )
                self._broadcast(
                    deployment_id,
                    {
                        "type": "incident",
                        "stage": self.name.lower(),
                        "severity": "high",
                        "message": incidents[0]["message"],
                        "ts": int(time.time()),
                    },
                )

        issue_url = None
        if incidents and repo_url and os.getenv("GITHUB_TOKEN"):
            title = incidents[0]["message"][:70]
            body = (
                f"Deployment ID: {deployment_id}\n\n"
                f"Commit: {commit_sha}\n\n"
                f"URL: {context.get('deployment_url')}\n\n"
                f"Details: {json.dumps(incidents[0], ensure_ascii=False)}\n\n"
                f"Proposal: {json.dumps(proposal or {}, ensure_ascii=False)}\n"
            )
            issue_url = self._open_github_issue(repo_url, title, body)
            if deployment_id and issue_url:
                self._broadcast(
                    deployment_id,
                    {
                        "type": "github",
                        "action": "issue_created",
                        "url": issue_url,
                        "ts": int(time.time()),
                    },
                )

        # Optional email to commit author
        if incidents and commit_sha:
            author_str = _git_show_author(workdir, commit_sha)
            to_addr = self._parse_email(author_str)
            if to_addr:
                subject = f"Incident: {incidents[0]['message'][:60]}"
                body = (
                    f"Deployment ID: {deployment_id}\n"
                    f"Repo: {repo_url}\nCommit: {commit_sha}\n"
                    f"Deployment URL: {context.get('deployment_url')}\n\n"
                    f"Incident: {incidents[0]['message']}\n\n"
                    f"Proposal: {json.dumps((proposal or {}), ensure_ascii=False)}\n\n"
                    f"Issue: {issue_url or 'n/a'}\n"
                )
                sent = self._send_incident_email(to_addr, subject, body)
                if deployment_id and sent:
                    self._broadcast(
                        deployment_id,
                        {
                            "type": "incident",
                            "stage": self.name.lower(),
                            "severity": "info",
                            "message": f"Email sent to {to_addr}",
                            "ts": int(time.time()),
                        },
                    )

        # Optional PR with proposed tests
        pr_url = None
        test_files = []
        if isinstance(context.get("test_proposals"), list):
            for t in context.get("test_proposals"):
                if isinstance(t, dict) and t.get("path") and t.get("content"):
                    test_files.append({"path": t["path"], "content": t["content"]})
        if incidents and repo_url and commit_sha and test_files and os.getenv("GITHUB_TOKEN"):
            pr_title = f"Add smoke tests (AgentOps)"
            pr_body = (
                f"Automated test proposals generated due to incident.\n\n"
                f"Proposal: {json.dumps((proposal or {}), ensure_ascii=False)}\n"
            )
            pr_url = self._create_github_pr(
                repo_url=repo_url, base_sha=commit_sha, title=pr_title, body=pr_body, files=test_files
            )
            if deployment_id and pr_url:
                self._broadcast(
                    deployment_id,
                    {"type": "github", "action": "pr_opened", "url": pr_url, "ts": int(time.time())},
                )

        new_ctx = {**context}
        if http_status is not None:
            new_ctx["http_status"] = int(http_status)
            new_ctx["healthy"] = bool(healthy)
        if incidents:
            new_ctx["incidents"] = incidents
        if issue_url:
            new_ctx["github_issue_url"] = issue_url
        if pr_url:
            new_ctx["github_pr_url"] = pr_url
        if proposal:
            new_ctx["incident_proposal"] = proposal
        return new_ctx


