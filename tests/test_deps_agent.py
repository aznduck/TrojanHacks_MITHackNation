import json
from unittest.mock import Mock, patch

from agents.deps import DependencyAnalyzer


class TestDependencyAnalyzer:
    def test_parse_requirements_basic(self):
        analyzer = DependencyAnalyzer(name="deps", description="parse")
        text = """
        fastapi==0.104.1
        uvicorn>=0.24
        httpx~=0.27
        numpy<2.0
        pandas>2.0
        pydantic<=2.7
        simplejson
        # comment
        """.strip()
        deps = analyzer._parse_requirements(text)
        assert deps["fastapi"] == "==0.104.1"
        assert deps["uvicorn"] == ">=0.24"
        assert deps["httpx"] == "~=0.27"
        assert deps["numpy"] == "<2.0"
        assert deps["pandas"] == ">2.0"
        assert deps["pydantic"] == "<=2.7"
        assert deps["simplejson"] == "*"

    def test_parse_requirements_ignores_empty_and_comments(self):
        analyzer = DependencyAnalyzer(name="deps", description="parse")
        text = """
        \n  # leading comment\n\n   
        requests==2.32.0   
        # trailing comment
        """
        deps = analyzer._parse_requirements(text)
        assert list(deps.keys()) == ["requests"]
        assert deps["requests"] == "==2.32.0"

    def test_parse_package_json_basic(self):
        analyzer = DependencyAnalyzer(name="deps", description="parse")
        pkg = {
            "dependencies": {"react": "^18.0.0"},
            "devDependencies": {"jest": "^29.0.0"},
            "optionalDependencies": {"fsevents": "^2.0.0"},
        }
        deps = analyzer._parse_package_json(json.dumps(pkg))
        assert deps["react"] == "^18.0.0"
        assert deps["jest"] == "^29.0.0"
        assert deps["fsevents"] == "^2.0.0"

    def test_parse_package_json_corrupted(self):
        analyzer = DependencyAnalyzer(name="deps", description="parse")
        deps = analyzer._parse_package_json("{not json")
        assert deps == {}

    def test_run_prefers_package_json_over_requirements(self, tmp_path):
        analyzer = DependencyAnalyzer(name="deps", description="parse")
        (tmp_path / "package.json").write_text(json.dumps({"dependencies": {"express": "^4.18.0"}}))
        (tmp_path / "requirements.txt").write_text("fastapi==0.104.1\n")
        ctx = {"workdir": str(tmp_path)}
        out = analyzer.run(ctx)
        assert out["package_manager"] == "npm"
        assert "express" in out["dependencies"]
        assert "fastapi" not in out["dependencies"]

    def test_run_requirements_only(self, tmp_path):
        analyzer = DependencyAnalyzer(name="deps", description="parse")
        (tmp_path / "requirements.txt").write_text("fastapi==0.104.1\n")
        ctx = {"workdir": str(tmp_path)}
        out = analyzer.run(ctx)
        assert out["package_manager"] == "pip"
        assert out["dependencies"].get("fastapi") == "==0.104.1"

    def test_run_neither_present(self, tmp_path):
        analyzer = DependencyAnalyzer(name="deps", description="parse")
        ctx = {"workdir": str(tmp_path)}
        out = analyzer.run(ctx)
        assert out["package_manager"] is None
        assert out["dependencies"] == {}

    @patch("agents.deps.DependencyAnalyzer.build_agent")
    def test_ai_dependency_notes_for_package_json(self, mock_build_agent, tmp_path):
        analyzer = DependencyAnalyzer(name="deps", description="parse")
        (tmp_path / "package.json").write_text(json.dumps({"dependencies": {"leftpad": "^1.0.0"}}))
        mock_executor = Mock()
        mock_executor.invoke.return_value = {
            "output": json.dumps({
                "dependency_notes": [
                    {"name": "leftpad", "issue": "deprecated", "recommendation": "replace with native string methods"}
                ]
            })
        }
        mock_build_agent.return_value = mock_executor
        out = analyzer.run({"workdir": str(tmp_path)})
        assert any(n.get("name") == "leftpad" for n in out.get("dependency_notes", []))

    @patch("agents.deps.DependencyAnalyzer.build_agent")
    def test_ai_dependency_notes_for_requirements(self, mock_build_agent, tmp_path):
        analyzer = DependencyAnalyzer(name="deps", description="parse")
        (tmp_path / "requirements.txt").write_text("django==3.2.0\n")
        mock_executor = Mock()
        mock_executor.invoke.return_value = {
            "output": json.dumps({
                "dependency_notes": [
                    {"name": "django", "issue": "outdated", "recommendation": "upgrade to 4.x"}
                ]
            })
        }
        mock_build_agent.return_value = mock_executor
        out = analyzer.run({"workdir": str(tmp_path)})
        assert any(n.get("name") == "django" for n in out.get("dependency_notes", []))


