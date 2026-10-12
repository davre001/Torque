"""Explicit execution policy, configured independently of HTTP settings."""
from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
from pydantic import Field, field_validator
from backend.config import ROOT
from backend.models import PipelineError, Record

class Recipe(Record):
    repository_setup: dict | None = None
    image: str
    command: list[str] = Field(min_length=1,max_length=30)
    context_files: list[str] = Field(min_length=1,max_length=30)
    investigation_terms: dict[str,list[str]] = Field(default_factory=dict)
    editable_files: list[str] = Field(min_length=1,max_length=10)
    acceptance_criteria: list[str] = Field(min_length=1,max_length=12)
    suite_directory: str
    timeout_seconds: int = Field(default=120,ge=1,le=600)
    require_baseline_failure: bool = True

    @field_validator("image")
    @classmethod
    def immutable_image(cls,value):
        import re
        if value == "remote-managed":
            return value
        if not re.fullmatch(r"(?:[a-zA-Z0-9./:_-]+@)?sha256:[a-f0-9]{64}",value):
            raise ValueError("Test image must use an immutable sha256 digest or local image ID")
        return value

@dataclass(frozen=True)
class Limits:
    max_calls: int = 12
    max_tokens: int = 100000
    max_cost_usd: float = 2.0
    max_seconds: int = 900
    max_output_tokens: int = 4096
    max_patch_bytes: int = 100000
    recovery_retries: int = 2
    transport_retries: int = 1

    def __post_init__(self):
        if any(x <= 0 for x in (self.max_calls,self.max_tokens,self.max_cost_usd,self.max_seconds,self.max_output_tokens,self.max_patch_bytes)):
            raise ValueError("Execution limits must be positive")
        if not math.isfinite(self.max_cost_usd) or not 0 <= self.recovery_retries <= 2 or not 0 <= self.transport_retries <= 2:
            raise ValueError("Invalid execution retry or cost limits")

    @classmethod
    def load(cls):
        return cls(max_cost_usd=float(os.getenv("TORQUE_MAX_COST_USD","2")),
                   max_tokens=int(os.getenv("TORQUE_MAX_TOKENS","100000")),
                   max_seconds=int(os.getenv("TORQUE_MAX_SECONDS","900")),
                   max_calls=int(os.getenv("TORQUE_MAX_CALLS","12")),
                   max_patch_bytes=int(os.getenv("TORQUE_MAX_PATCH_BYTES","100000")),
                   recovery_retries=int(os.getenv("TORQUE_RECOVERY_RETRIES","2")))

def load_recipes(path=None):
    path = path or os.getenv("TORQUE_RECIPES_FILE","")
    if not path:
        raise PipelineError("Set TORQUE_RECIPES_FILE to an operator-reviewed test recipe file")
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        if not isinstance(data,dict):
            raise ValueError("Expected repository mapping")
        return {slug.lower():Recipe.model_validate(recipe) for slug,recipe in data.items()}
    except (OSError,ValueError) as exc:
        raise PipelineError("Test recipes are missing or invalid; inspect the recipe configuration") from exc

def workspace_root():
    return ROOT / "var" / "workspaces"
