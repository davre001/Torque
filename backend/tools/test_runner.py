"""Public test-runner interface; execution is Docker-only."""
from backend.models import TestResult
from backend.tools.sandbox import DockerRunner

__all__ = ["DockerRunner", "TestResult"]
