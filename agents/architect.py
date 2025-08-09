import json
import os
from typing import Dict, Any, List
from langchain.tools import Tool
from agents.base import BaseAgent


class ArchitectAgent(BaseAgent):
    """Agent responsible for generating Dockerfiles, configs, and CI/CD pipelines."""

    def __init__(self, llm=None):
        super().__init__(
            name="Architect",
            description="Generates Dockerfiles, configuration files, and CI/CD pipelines based on project analysis",
            llm=llm,
            temperature=0.1
        )

    def setup_tools(self):
        """Setup tools for the Architect agent."""
        return [
            Tool(
                name="analyze_project",
                func=self._analyze_project,
                description="Analyze project structure to determine technology stack and requirements"
            ),
            Tool(
                name="generate_dockerfile",
                func=self._generate_dockerfile,
                description="Generate a Dockerfile based on project requirements"
            ),
            Tool(
                name="generate_ci_cd_pipeline",
                func=self._generate_ci_cd_pipeline,
                description="Generate CI/CD pipeline configuration (GitHub Actions, GitLab CI, etc.)"
            ),
            Tool(
                name="generate_docker_compose",
                func=self._generate_docker_compose,
                description="Generate docker-compose.yml for multi-container applications"
            ),
            Tool(
                name="generate_kubernetes_manifests",
                func=self._generate_kubernetes_manifests,
                description="Generate Kubernetes deployment manifests"
            )
        ]

    def _analyze_project(self, project_path: str) -> str:
        """Analyze project structure to identify technology stack."""
        analysis = {
            "languages": [],
            "frameworks": [],
            "package_managers": [],
            "databases": [],
            "services": []
        }
        
        # Check for common project files
        files_to_check = {
            "package.json": {"type": "node", "package_manager": "npm/yarn"},
            "requirements.txt": {"type": "python", "package_manager": "pip"},
            "Pipfile": {"type": "python", "package_manager": "pipenv"},
            "poetry.lock": {"type": "python", "package_manager": "poetry"},
            "go.mod": {"type": "go", "package_manager": "go modules"},
            "pom.xml": {"type": "java", "package_manager": "maven"},
            "build.gradle": {"type": "java", "package_manager": "gradle"},
            "Gemfile": {"type": "ruby", "package_manager": "bundler"},
            "Cargo.toml": {"type": "rust", "package_manager": "cargo"},
            "composer.json": {"type": "php", "package_manager": "composer"}
        }
        
        for file, info in files_to_check.items():
            if os.path.exists(os.path.join(project_path, file)):
                analysis["languages"].append(info["type"])
                analysis["package_managers"].append(info["package_manager"])
                
                # Read file for framework detection
                if file == "package.json":
                    try:
                        with open(os.path.join(project_path, file), 'r') as f:
                            package_data = json.load(f)
                            deps = {**package_data.get("dependencies", {}), **package_data.get("devDependencies", {})}
                            
                            if "react" in deps:
                                analysis["frameworks"].append("react")
                            if "vue" in deps:
                                analysis["frameworks"].append("vue")
                            if "next" in deps:
                                analysis["frameworks"].append("nextjs")
                            if "express" in deps:
                                analysis["frameworks"].append("express")
                            if "@angular/core" in deps:
                                analysis["frameworks"].append("angular")
                    except:
                        pass
                        
                elif file == "requirements.txt":
                    try:
                        with open(os.path.join(project_path, file), 'r') as f:
                            requirements = f.read().lower()
                            if "django" in requirements:
                                analysis["frameworks"].append("django")
                            if "flask" in requirements:
                                analysis["frameworks"].append("flask")
                            if "fastapi" in requirements:
                                analysis["frameworks"].append("fastapi")
                            if "pytest" in requirements:
                                analysis["frameworks"].append("pytest")
                    except:
                        pass
        
        return json.dumps(analysis)

    def _generate_dockerfile(self, context: str) -> str:
        """Generate a Dockerfile based on project analysis."""
        try:
            project_info = json.loads(context)
        except:
            project_info = {"languages": ["python"], "frameworks": [], "package_managers": ["pip"]}
        
        dockerfiles = {
            "python": self._python_dockerfile,
            "node": self._node_dockerfile,
            "go": self._go_dockerfile,
            "java": self._java_dockerfile,
            "ruby": self._ruby_dockerfile,
            "rust": self._rust_dockerfile,
            "php": self._php_dockerfile
        }
        
        # Get the primary language
        language = project_info.get("languages", ["python"])[0]
        
        # Generate appropriate Dockerfile
        dockerfile_generator = dockerfiles.get(language, self._python_dockerfile)
        return dockerfile_generator(project_info)

    def _python_dockerfile(self, project_info: Dict) -> str:
        """Generate Python Dockerfile."""
        frameworks = project_info.get("frameworks", [])
        package_manager = next((pm for pm in project_info.get("package_managers", []) if "pip" in pm or "poetry" in pm or "pipenv" in pm), "pip")
        
        dockerfile = """# Python Application Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

"""
        
        if "poetry" in package_manager:
            dockerfile += """# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry config virtualenvs.create false && poetry install --no-dev

# Copy application code
COPY . .

# Run the application
"""
        elif "pipenv" in package_manager:
            dockerfile += """# Install Pipenv
RUN pip install pipenv

# Copy dependency files
COPY Pipfile Pipfile.lock ./

# Install dependencies
RUN pipenv install --system --deploy

# Copy application code
COPY . .

# Run the application
"""
        else:
            dockerfile += """# Copy dependency files
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run the application
"""
        
        # Add framework-specific commands
        if "fastapi" in frameworks:
            dockerfile += 'CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]'
        elif "flask" in frameworks:
            dockerfile += 'CMD ["python", "app.py"]'
        elif "django" in frameworks:
            dockerfile += 'CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]'
        else:
            dockerfile += 'CMD ["python", "main.py"]'
        
        return dockerfile

    def _node_dockerfile(self, project_info: Dict) -> str:
        """Generate Node.js Dockerfile."""
        frameworks = project_info.get("frameworks", [])
        
        dockerfile = """# Node.js Application Dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

"""
        
        # Add framework-specific build steps
        if "nextjs" in frameworks:
            dockerfile += """# Build Next.js application
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]"""
        elif "react" in frameworks or "vue" in frameworks or "angular" in frameworks:
            dockerfile += """# Build frontend application
RUN npm run build

# Use nginx to serve static files
FROM nginx:alpine
COPY --from=0 /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]"""
        else:
            dockerfile += """EXPOSE 3000

CMD ["node", "index.js"]"""
        
        return dockerfile

    def _go_dockerfile(self, project_info: Dict) -> str:
        """Generate Go Dockerfile."""
        return """# Go Application Dockerfile
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -o main .

# Final stage
FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

# Copy the binary from builder
COPY --from=builder /app/main .

EXPOSE 8080

CMD ["./main"]"""

    def _java_dockerfile(self, project_info: Dict) -> str:
        """Generate Java Dockerfile."""
        package_manager = next((pm for pm in project_info.get("package_managers", []) if "maven" in pm or "gradle" in pm), "maven")
        
        if "gradle" in package_manager:
            return """# Java Application Dockerfile with Gradle
FROM gradle:8-jdk17 AS builder

WORKDIR /app

# Copy gradle files
COPY build.gradle settings.gradle ./

# Download dependencies
RUN gradle dependencies --no-daemon

# Copy source code
COPY src ./src

# Build application
RUN gradle build --no-daemon

# Final stage
FROM openjdk:17-slim

WORKDIR /app

# Copy JAR from builder
COPY --from=builder /app/build/libs/*.jar app.jar

EXPOSE 8080

CMD ["java", "-jar", "app.jar"]"""
        else:
            return """# Java Application Dockerfile with Maven
FROM maven:3.9-openjdk-17 AS builder

WORKDIR /app

# Copy pom.xml
COPY pom.xml .

# Download dependencies
RUN mvn dependency:go-offline

# Copy source code
COPY src ./src

# Build application
RUN mvn package -DskipTests

# Final stage
FROM openjdk:17-slim

WORKDIR /app

# Copy JAR from builder
COPY --from=builder /app/target/*.jar app.jar

EXPOSE 8080

CMD ["java", "-jar", "app.jar"]"""

    def _ruby_dockerfile(self, project_info: Dict) -> str:
        """Generate Ruby Dockerfile."""
        return """# Ruby Application Dockerfile
FROM ruby:3.2-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Copy Gemfile
COPY Gemfile Gemfile.lock ./

# Install gems
RUN bundle install

# Copy application code
COPY . .

EXPOSE 3000

CMD ["ruby", "app.rb"]"""

    def _rust_dockerfile(self, project_info: Dict) -> str:
        """Generate Rust Dockerfile."""
        return """# Rust Application Dockerfile
FROM rust:1.73 AS builder

WORKDIR /app

# Copy Cargo files
COPY Cargo.toml Cargo.lock ./

# Build dependencies
RUN mkdir src && echo "fn main() {}" > src/main.rs
RUN cargo build --release
RUN rm -rf src

# Copy source code
COPY src ./src

# Build application
RUN touch src/main.rs
RUN cargo build --release

# Final stage
FROM debian:bookworm-slim

WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/target/release/app /usr/local/bin/app

EXPOSE 8080

CMD ["app"]"""

    def _php_dockerfile(self, project_info: Dict) -> str:
        """Generate PHP Dockerfile."""
        return """# PHP Application Dockerfile
FROM php:8.2-apache

WORKDIR /var/www/html

# Install PHP extensions
RUN docker-php-ext-install pdo pdo_mysql

# Enable Apache modules
RUN a2enmod rewrite

# Copy application code
COPY . .

# Install Composer dependencies
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer
RUN composer install --no-dev --optimize-autoloader

EXPOSE 80

CMD ["apache2-foreground"]"""

    def _generate_ci_cd_pipeline(self, context: str) -> str:
        """Generate CI/CD pipeline configuration."""
        try:
            project_info = json.loads(context)
        except:
            project_info = {"languages": ["python"], "frameworks": [], "package_managers": ["pip"]}
        
        # Generate GitHub Actions workflow by default
        return self._generate_github_actions(project_info)

    def _generate_github_actions(self, project_info: Dict) -> str:
        """Generate GitHub Actions workflow."""
        language = project_info.get("languages", ["python"])[0]
        
        workflow = """name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
"""
        
        if language == "python":
            workflow += """    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest --cov=./ --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
"""
        elif language == "node":
            workflow += """    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Run tests
      run: npm test
    
    - name: Run linter
      run: npm run lint
"""
        elif language == "go":
            workflow += """    - name: Set up Go
      uses: actions/setup-go@v4
      with:
        go-version: '1.21'
    
    - name: Install dependencies
      run: go mod download
    
    - name: Run tests
      run: go test -v ./...
    
    - name: Run linter
      run: |
        go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
        golangci-lint run
"""
        
        workflow += """
  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Log in to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: |
          ${{ secrets.DOCKER_USERNAME }}/${{ github.event.repository.name }}:latest
          ${{ secrets.DOCKER_USERNAME }}/${{ github.event.repository.name }}:${{ github.sha }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    
    steps:
    - name: Deploy to production
      run: |
        echo "Deploying to production..."
        # Add deployment commands here
"""
        
        return workflow

    def _generate_docker_compose(self, context: str) -> str:
        """Generate docker-compose.yml for multi-container applications."""
        try:
            project_info = json.loads(context)
        except:
            project_info = {"languages": ["python"], "frameworks": [], "services": []}
        
        compose = """version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://user:password@db:5432/appdb
    depends_on:
      - db
      - redis
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=appdb
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

volumes:
  postgres_data:
"""
        
        return compose

    def _generate_kubernetes_manifests(self, context: str) -> str:
        """Generate Kubernetes deployment manifests."""
        manifests = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-deployment
  labels:
    app: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: app
        image: myapp:latest
        ports:
        - containerPort: 8000
        env:
        - name: NODE_ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: app-service
spec:
  selector:
    app: myapp
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: LoadBalancer
---
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
stringData:
  database-url: "postgresql://user:password@db:5432/appdb"
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: app-deployment
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
"""
        
        return manifests

    def run(self, context):
        """Run the Architect agent with specific instructions."""
        instruction = (
            "Analyze the project and generate appropriate infrastructure files. "
            "Use the analyze_project tool first, then generate Dockerfile, CI/CD pipeline, "
            "and other necessary configuration files. Return a JSON with generated files."
        )
        
        executor = self.build_agent()
        raw = self._invoke(executor, instruction=instruction, context=context)
        return self._merge_delta_into_context(delta_json=raw, context=context)