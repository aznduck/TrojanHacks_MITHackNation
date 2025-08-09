import json
import os
from unittest.mock import Mock, patch
from agents.architect import ArchitectAgent
from agents.deps import DependencyAnalyzer

# Load environment variables for testing
from dotenv import load_dotenv
load_dotenv()


class TestArchitectAgent:
    """Test suite for the Architect agent."""

    def test_architect_agent_initialization(self):
        """Test that the Architect agent initializes correctly."""
        agent = ArchitectAgent()
        assert agent.name == "Architect"
        assert "Dockerfiles" in agent.description
        assert len(agent.tools) == 5

    def test_setup_tools(self):
        """Test that all required tools are set up."""
        agent = ArchitectAgent()
        tool_names = [tool.name for tool in agent.tools]
        
        expected_tools = [
            "analyze_project",
            "generate_dockerfile",
            "generate_ci_cd_pipeline",
            "generate_docker_compose",
            "generate_kubernetes_manifests"
        ]
        
        for tool_name in expected_tools:
            assert tool_name in tool_names

    def test_analyze_project_python(self, tmp_path):
        """Test project analysis for Python projects."""
        agent = ArchitectAgent()
        
        # Create test Python project structure
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("fastapi==0.104.1\nuvicorn==0.24.0\npytest==7.4.3")
        
        result = agent._analyze_project(str(tmp_path))
        analysis = json.loads(result)
        
        assert "python" in analysis["languages"]
        assert "pip" in analysis["package_managers"]
        assert "fastapi" in analysis["frameworks"]
        assert "pytest" in analysis["frameworks"]

    def test_analyze_project_node(self, tmp_path):
        """Test project analysis for Node.js projects."""
        agent = ArchitectAgent()
        
        # Create test Node.js project structure
        package_json = tmp_path / "package.json"
        package_json.write_text(json.dumps({
            "name": "test-app",
            "dependencies": {
                "react": "^18.0.0",
                "express": "^4.18.0"
            },
            "devDependencies": {
                "jest": "^29.0.0"
            }
        }))
        
        result = agent._analyze_project(str(tmp_path))
        analysis = json.loads(result)
        
        assert "node" in analysis["languages"]
        assert "npm/yarn" in analysis["package_managers"]
        assert "react" in analysis["frameworks"]
        assert "express" in analysis["frameworks"]

    def test_analyze_project_multiple_languages(self, tmp_path):
        """Test project analysis for multi-language projects."""
        agent = ArchitectAgent()
        
        # Create mixed project structure
        (tmp_path / "requirements.txt").write_text("django==4.2.0")
        (tmp_path / "package.json").write_text(json.dumps({"dependencies": {"vue": "^3.0.0"}}))
        (tmp_path / "go.mod").write_text("module example.com/app")
        
        result = agent._analyze_project(str(tmp_path))
        analysis = json.loads(result)
        
        assert "python" in analysis["languages"]
        assert "node" in analysis["languages"]
        assert "go" in analysis["languages"]
        assert "django" in analysis["frameworks"]
        assert "vue" in analysis["frameworks"]

    def test_generate_python_dockerfile_pip(self):
        """Test Python Dockerfile generation with pip."""
        agent = ArchitectAgent()
        context = json.dumps({
            "languages": ["python"],
            "frameworks": ["fastapi"],
            "package_managers": ["pip"]
        })
        
        dockerfile = agent._generate_dockerfile(context)
        
        assert "FROM python:3.11-slim" in dockerfile
        assert "COPY requirements.txt" in dockerfile
        assert "pip install --no-cache-dir -r requirements.txt" in dockerfile
        assert 'CMD ["uvicorn", "main:app"' in dockerfile

    def test_generate_python_dockerfile_poetry(self):
        """Test Python Dockerfile generation with Poetry."""
        agent = ArchitectAgent()
        context = json.dumps({
            "languages": ["python"],
            "frameworks": ["django"],
            "package_managers": ["poetry"]
        })
        
        dockerfile = agent._generate_dockerfile(context)
        
        assert "pip install poetry" in dockerfile
        assert "COPY pyproject.toml poetry.lock*" in dockerfile
        assert "poetry install --no-dev" in dockerfile
        assert 'CMD ["python", "manage.py", "runserver"' in dockerfile

    def test_generate_node_dockerfile_nextjs(self):
        """Test Node.js Dockerfile generation for Next.js."""
        agent = ArchitectAgent()
        context = json.dumps({
            "languages": ["node"],
            "frameworks": ["nextjs"],
            "package_managers": ["npm/yarn"]
        })
        
        dockerfile = agent._generate_dockerfile(context)
        
        assert "FROM node:18-alpine" in dockerfile
        assert "npm ci --only=production" in dockerfile
        assert "npm run build" in dockerfile
        assert 'CMD ["npm", "start"]' in dockerfile

    def test_generate_node_dockerfile_react(self):
        """Test Node.js Dockerfile generation for React."""
        agent = ArchitectAgent()
        context = json.dumps({
            "languages": ["node"],
            "frameworks": ["react"],
            "package_managers": ["npm/yarn"]
        })
        
        dockerfile = agent._generate_dockerfile(context)
        
        assert "FROM node:18-alpine" in dockerfile
        assert "npm run build" in dockerfile
        assert "FROM nginx:alpine" in dockerfile
        assert "COPY --from=0 /app/build /usr/share/nginx/html" in dockerfile

    def test_generate_go_dockerfile(self):
        """Test Go Dockerfile generation."""
        agent = ArchitectAgent()
        context = json.dumps({
            "languages": ["go"],
            "frameworks": [],
            "package_managers": ["go modules"]
        })
        
        dockerfile = agent._generate_dockerfile(context)
        
        assert "FROM golang:1.21-alpine AS builder" in dockerfile
        assert "go mod download" in dockerfile
        assert "CGO_ENABLED=0 GOOS=linux go build" in dockerfile
        assert "FROM alpine:latest" in dockerfile

    def test_generate_java_dockerfile_maven(self):
        """Test Java Dockerfile generation with Maven."""
        agent = ArchitectAgent()
        context = json.dumps({
            "languages": ["java"],
            "frameworks": [],
            "package_managers": ["maven"]
        })
        
        dockerfile = agent._generate_dockerfile(context)
        
        assert "FROM maven:3.9-openjdk-17 AS builder" in dockerfile
        assert "mvn dependency:go-offline" in dockerfile
        assert "mvn package -DskipTests" in dockerfile
        assert "FROM openjdk:17-slim" in dockerfile

    def test_generate_java_dockerfile_gradle(self):
        """Test Java Dockerfile generation with Gradle."""
        agent = ArchitectAgent()
        context = json.dumps({
            "languages": ["java"],
            "frameworks": [],
            "package_managers": ["gradle"]
        })
        
        dockerfile = agent._generate_dockerfile(context)
        
        assert "FROM gradle:8-jdk17 AS builder" in dockerfile
        assert "gradle dependencies --no-daemon" in dockerfile
        assert "gradle build --no-daemon" in dockerfile

    def test_generate_github_actions_python(self):
        """Test GitHub Actions workflow generation for Python."""
        agent = ArchitectAgent()
        project_info = {
            "languages": ["python"],
            "frameworks": ["fastapi"],
            "package_managers": ["pip"]
        }
        
        workflow = agent._generate_github_actions(project_info)
        
        assert "name: CI/CD Pipeline" in workflow
        assert "uses: actions/setup-python@v4" in workflow
        assert "python-version: '3.11'" in workflow
        assert "pip install -r requirements.txt" in workflow
        assert "pytest --cov=./" in workflow

    def test_generate_github_actions_node(self):
        """Test GitHub Actions workflow generation for Node.js."""
        agent = ArchitectAgent()
        project_info = {
            "languages": ["node"],
            "frameworks": ["react"],
            "package_managers": ["npm"]
        }
        
        workflow = agent._generate_github_actions(project_info)
        
        assert "uses: actions/setup-node@v3" in workflow
        assert "node-version: '18'" in workflow
        assert "npm ci" in workflow
        assert "npm test" in workflow
        assert "npm run lint" in workflow

    def test_generate_github_actions_go(self):
        """Test GitHub Actions workflow generation for Go."""
        agent = ArchitectAgent()
        project_info = {
            "languages": ["go"],
            "frameworks": [],
            "package_managers": ["go modules"]
        }
        
        workflow = agent._generate_github_actions(project_info)
        
        assert "uses: actions/setup-go@v4" in workflow
        assert "go-version: '1.21'" in workflow
        assert "go mod download" in workflow
        assert "go test -v ./..." in workflow

    def test_generate_docker_compose(self):
        """Test docker-compose.yml generation."""
        agent = ArchitectAgent()
        context = json.dumps({
            "languages": ["python"],
            "frameworks": ["django"],
            "services": ["postgres", "redis"]
        })
        
        compose = agent._generate_docker_compose(context)
        
        assert "version: '3.8'" in compose
        assert "services:" in compose
        assert "app:" in compose
        assert "db:" in compose
        assert "redis:" in compose
        assert "postgres:15-alpine" in compose
        assert "redis:7-alpine" in compose
        assert "volumes:" in compose
        assert "postgres_data:" in compose

    def test_generate_kubernetes_manifests(self):
        """Test Kubernetes manifests generation."""
        agent = ArchitectAgent()
        context = json.dumps({})
        
        manifests = agent._generate_kubernetes_manifests(context)
        
        assert "kind: Deployment" in manifests
        assert "kind: Service" in manifests
        assert "kind: Secret" in manifests
        assert "kind: HorizontalPodAutoscaler" in manifests
        assert "replicas: 3" in manifests
        assert "containerPort: 8000" in manifests
        assert "type: LoadBalancer" in manifests

    @patch('agents.architect.ArchitectAgent.build_agent')
    def test_run_method(self, mock_build_agent):
        """Test the run method with mocked LLM interaction."""
        agent = ArchitectAgent()
        
        # Mock the executor
        mock_executor = Mock()
        mock_executor.invoke.return_value = {
            "output": json.dumps({
                "dockerfile": "FROM python:3.11-slim...",
                "ci_cd_pipeline": "name: CI/CD Pipeline...",
                "docker_compose": "version: '3.8'...",
                "status": "Infrastructure files generated successfully"
            })
        }
        mock_build_agent.return_value = mock_executor
        
        context = {
            "repository": "https://github.com/user/repo",
            "branch": "main"
        }
        
        result = agent.run(context)
        
        assert "dockerfile" in result
        assert "ci_cd_pipeline" in result
        assert "docker_compose" in result
        assert "status" in result
        assert result["repository"] == "https://github.com/user/repo"

    def test_dockerfile_generation_with_invalid_context(self):
        """Test Dockerfile generation with invalid context."""
        agent = ArchitectAgent()
        
        # Test with invalid JSON
        dockerfile = agent._generate_dockerfile("invalid json")
        
        # Should fall back to Python default
        assert "FROM python:3.11-slim" in dockerfile
        assert "requirements.txt" in dockerfile

    def test_ci_cd_pipeline_generation_with_invalid_context(self):
        """Test CI/CD pipeline generation with invalid context."""
        agent = ArchitectAgent()
        
        # Test with invalid JSON
        workflow = agent._generate_ci_cd_pipeline("invalid json")
        
        # Should fall back to Python default
        assert "name: CI/CD Pipeline" in workflow
        assert "uses: actions/setup-python@v4" in workflow

    def test_analyze_project_empty_directory(self, tmp_path):
        """Test project analysis on empty directory."""
        agent = ArchitectAgent()
        
        result = agent._analyze_project(str(tmp_path))
        analysis = json.loads(result)
        
        assert analysis["languages"] == []
        assert analysis["frameworks"] == []
        assert analysis["package_managers"] == []

    def test_analyze_project_with_corrupted_files(self, tmp_path):
        """Test project analysis with corrupted package.json."""
        agent = ArchitectAgent()
        
        # Create corrupted package.json
        package_json = tmp_path / "package.json"
        package_json.write_text("not valid json{")
        
        result = agent._analyze_project(str(tmp_path))
        analysis = json.loads(result)
        
        # Should still detect Node.js but not frameworks
        assert "node" in analysis["languages"]
        assert "npm/yarn" in analysis["package_managers"]
        assert analysis["frameworks"] == []  # No frameworks detected due to parse error


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