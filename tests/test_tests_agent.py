import json
from unittest.mock import patch

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


