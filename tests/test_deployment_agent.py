from unittest.mock import patch

from agents.deployment import DeploymentAgent


class TestDeploymentAgent:
    @patch("agents.deployment._which", return_value=None)
    def test_no_vercel_cli(self, mock_which, tmp_path):
        agent = DeploymentAgent()
        out = agent.run({"workdir": str(tmp_path)})
        assert out.get("error") == "vercel cli not available"

    @patch("agents.deployment._which", return_value=True)
    def test_missing_token(self, mock_which, tmp_path, monkeypatch):
        monkeypatch.delenv("VERCEL_TOKEN", raising=False)
        agent = DeploymentAgent()
        out = agent.run({"workdir": str(tmp_path)})
        assert out.get("error") == "VERCEL_TOKEN not set"

    @patch("agents.deployment._which", return_value=True)
    @patch("subprocess.run")
    def test_deploy_success(self, mock_run, mock_which, tmp_path, monkeypatch):
        monkeypatch.setenv("VERCEL_TOKEN", "t")

        class R:
            returncode = 0
            stdout = "Deployment ready! https://example.vercel.app"
            stderr = ""

        mock_run.return_value = R()
        agent = DeploymentAgent()
        out = agent.run({"workdir": str(tmp_path)})
        assert out.get("deployment_url", "").startswith("http")
        assert "vercel_output" in out

    @patch("agents.deployment._which", return_value=True)
    @patch("subprocess.run")
    def test_deploy_fail(self, mock_run, mock_which, tmp_path, monkeypatch):
        monkeypatch.setenv("VERCEL_TOKEN", "t")

        class R:
            returncode = 1
            stdout = "error"
            stderr = ""

        mock_run.return_value = R()
        agent = DeploymentAgent()
        out = agent.run({"workdir": str(tmp_path)})
        assert out.get("error") == "deployment failed"


