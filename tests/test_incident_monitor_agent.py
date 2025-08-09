from unittest.mock import patch, Mock

from agents.incident_monitor import IncidentMonitorAgent


class TestIncidentMonitorAgent:
    @patch("agents.incident_monitor._http_get_status", return_value=(200, None))
    def test_healthy(self, mock_get, tmp_path):
        agent = IncidentMonitorAgent(attempts=1)
        out = agent.run({
            "workdir": str(tmp_path),
            "deployment_id": "d",
            "repo_url": "https://github.com/org/repo",
            "commit_sha": "deadbeef",
            "deployment_url": "https://example.com",
        })
        assert out.get("healthy") in (True, None)  # healthy True or unchanged if not set

    @patch("agents.incident_monitor._http_get_status", return_value=(500, None))
    def test_unhealthy_incident(self, mock_get, tmp_path):
        agent = IncidentMonitorAgent(attempts=1)
        out = agent.run({
            "workdir": str(tmp_path),
            "deployment_id": "d",
            "repo_url": "https://github.com/org/repo",
            "commit_sha": "deadbeef",
            "deployment_url": "https://example.com",
        })
        assert out.get("healthy") is False
        assert out.get("incidents")

    @patch("agents.incident_monitor._http_get_status", return_value=(None, "err"))
    def test_unreachable_incident(self, mock_get, tmp_path):
        agent = IncidentMonitorAgent(attempts=1)
        out = agent.run({
            "workdir": str(tmp_path),
            "deployment_id": "d",
            "repo_url": "https://github.com/org/repo",
            "commit_sha": "deadbeef",
            "deployment_url": "https://example.com",
        })
        assert out.get("healthy") is False
        assert out.get("incidents")

    @patch("agents.incident_monitor._http_get_status", return_value=(500, None))
    @patch("agents.incident_monitor.IncidentMonitorAgent.build_agent")
    def test_proposal_generated(self, mock_build_agent, mock_get, tmp_path):
        agent = IncidentMonitorAgent(attempts=1)
        mock_executor = Mock()
        mock_executor.invoke.return_value = {
            "output": "{\"proposal\": {\"summary\": \"Roll back\", \"steps\": [\"revert\"]}}"
        }
        mock_build_agent.return_value = mock_executor
        out = agent.run({
            "workdir": str(tmp_path),
            "repo_url": "https://github.com/org/repo",
            "commit_sha": "deadbeef",
            "deployment_url": "https://example.com",
        })
        assert out.get("incident_proposal", {}).get("summary") == "Roll back"


