"""Run states and strict GitHub issue validation."""
from enum import StrEnum
import re
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class Status(StrEnum):
    QUEUED = "queued"
    INVESTIGATING = "investigating"
    IMPLEMENTING = "implementing"
    VERIFYING = "verifying"
    RECOVERING = "recovering"
    READY = "ready_to_publish"
    PUBLISHING = "publishing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"

TERMINAL = {Status.READY, Status.COMPLETED, Status.FAILED, Status.CANCELLED, Status.INTERRUPTED}
ISSUE = re.compile(r"https://github\.com/([A-Za-z0-9][A-Za-z0-9-]{0,38})/([A-Za-z0-9_.-]{1,100})/issues/([1-9][0-9]*)/?\Z")

def parse_issue(url: str):
    match = ISSUE.fullmatch(url)
    if not match or match[2] in {".", ".."}:
        raise ValueError("Expected https://github.com/owner/repository/issues/positive-number")
    return match[1], match[2], int(match[3])

class SubmitRun(BaseModel):
    issue_url: str

    @field_validator("issue_url")
    @classmethod
    def validate_issue(cls, value):
        owner, repo, number = parse_issue(value)
        return f"https://github.com/{owner}/{repo}/issues/{number}"

class LeaseLost(RuntimeError):
    pass

class Conflict(ValueError):
    pass

class AdmissionDenied(Conflict):
    pass

class Cancelled(RuntimeError):
    pass

class PipelineError(RuntimeError):
    """Safe operator-facing error; must contain no provider exception payload."""

class BudgetExceeded(PipelineError):
    pass

class Record(BaseModel):
    model_config = ConfigDict(extra="forbid")

class Plan(Record):
    summary: str = Field(min_length=1,max_length=4000)
    acceptance_criteria: list[str] = Field(min_length=1,max_length=12)
    files: list[str] = Field(min_length=1,max_length=10)

class Replacement(Record):
    search: str = Field(min_length=1,max_length=20000)
    replacement: str = Field(max_length=20000)

class Edit(Record):
    path: str
    original_sha256: str = Field(pattern="^[0-9a-f]{64}$")
    content: str | None = None
    replacements: list[Replacement] | None = Field(default=None,min_length=1,max_length=20)

    @model_validator(mode="after")
    def one_edit_format(self):
        if (self.content is None) == (self.replacements is None):
            raise ValueError("Specify either content or replacements")
        return self

class Patch(Record):
    summary: str = Field(min_length=1,max_length=4000)
    edits: list[Edit] = Field(min_length=1,max_length=10)

class Review(Record):
    approved: bool
    rationale: str = Field(min_length=1,max_length=4000)
    satisfied_criteria: list[int]

class Recovery(Record):
    strategy: str = Field(min_length=1,max_length=4000)

class TestResult(Record):
    exit_code: int
    output: str
    timed_out: bool = False
    command: list[str]
    failure_kind: Literal["assertion","infrastructure","timeout"] | None = None
    assertions_passed: int = Field(default=0,ge=0)

    @property
    def passed(self):
        return self.exit_code == 0 and not self.timed_out and self.failure_kind is None
