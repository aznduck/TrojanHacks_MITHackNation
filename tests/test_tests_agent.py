import json
from unittest.mock import patch, Mock

from agents.tests import TestSuiteAgent


class TestTestSuiteAgent:
    def test_detect_none(self, tmp_path):
        agent = TestSuiteAgent()
        cmd, kind = agent._detect_command(str(tmp_path))
        assert cmd == ""
        assert kind == "none"

    @patch("agents.tests._which", return_value=True)
    def test_detect_node(self, mock_which, tmp_path):
        (tmp_path / "package.json").write_text(json.dumps({"scripts": {"test": "jest"}}))
        agent = TestSuiteAgent()
        cmd, kind = agent._detect_command(str(tmp_path))
        assert "npm test" in cmd
        assert kind == "node"

    @patch("agents.tests._which", return_value=True)
    def test_detect_python(self, mock_which, tmp_path):
        (tmp_path / "requirements.txt").write_text("pytest==8.0.0\n")
        agent = TestSuiteAgent()
        cmd, kind = agent._detect_command(str(tmp_path))
        assert "pytest" in cmd
        assert kind == "python"

    @patch("subprocess.run")
    def test_run_cmd_success(self, mock_run, tmp_path):
        class R:
            returncode = 0
            stdout = "ok"
            stderr = ""

        mock_run.return_value = R()
        agent = TestSuiteAgent()
        ok, out = agent._run_cmd("echo test", str(tmp_path))
        assert ok is True
        assert "$ echo test" in out

    @patch("subprocess.run")
    def test_run_cmd_failure(self, mock_run, tmp_path):
        class R:
            returncode = 1
            stdout = "fail"
            stderr = "boom"

        mock_run.return_value = R()
        agent = TestSuiteAgent()
        ok, out = agent._run_cmd("echo test", str(tmp_path))
        assert ok is False
        assert "boom" in out

    @patch("agents.tests.TestSuiteAgent.build_agent")
    def test_ai_test_proposals_when_no_tests(self, mock_build_agent, tmp_path):
        # No package.json or requirements.txt → triggers AI proposals
        mock_executor = Mock()
        mock_executor.invoke.return_value = {
            "output": json.dumps({
                "test_proposals": [
                    {"path": "tests/test_smoke.py", "language": "python", "content": "def test_true(): assert True"}
                ]
            })
        }
        mock_build_agent.return_value = mock_executor
        agent = TestSuiteAgent()
        ctx = {"workdir": str(tmp_path)}
        out = agent.run(ctx)
        assert "test_proposals" in out
        assert out["test_proposals"][0]["path"].endswith("test_smoke.py")


