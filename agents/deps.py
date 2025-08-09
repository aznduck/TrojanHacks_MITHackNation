import os
import json
import re

from .base import BaseAgent


class DependencyAnalyzer(BaseAgent):
    def setup_tools(self):
        return []

    def _read_text(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None

    def _parse_requirements(self, text):
        deps = {}
        if not text:
            return deps
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = re.split(r"(==|>=|<=|~=|>|<)", line, maxsplit=1)
            if m:
                name = m[0].strip()
                version = "".join(m[1:]).strip() if len(m) > 1 else ""
                if name:
                    deps[name] = version or "*"
        return deps

    def _parse_package_json(self, text):
        try:
            data = json.loads(text)
        except Exception:
            return {}
        deps = {}
        for key in ("dependencies", "devDependencies", "optionalDependencies"):
            section = data.get(key) or {}
            if isinstance(section, dict):
                deps.update(section)
        return deps

    def run(self, context):
        workdir = context.get("workdir") or os.getcwd()
        pkg_json_path = os.path.join(workdir, "package.json")
        reqs_path = os.path.join(workdir, "requirements.txt")

        if os.path.isfile(pkg_json_path):
            text = self._read_text(pkg_json_path)
            deps = self._parse_package_json(text or "{}")
            delta = {"package_manager": "npm", "dependencies": deps}
            return {**context, **delta}

        if os.path.isfile(reqs_path):
            text = self._read_text(reqs_path)
            deps = self._parse_requirements(text or "")
            delta = {"package_manager": "pip", "dependencies": deps}
            return {**context, **delta}

        return {**context, "dependencies": {}, "package_manager": None}


