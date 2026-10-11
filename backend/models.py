"""Run states and strict GitHub issue validation."""
from enum import StrEnum
import re
from pydantic import BaseModel, field_validator

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

class Cancelled(RuntimeError):
    pass
