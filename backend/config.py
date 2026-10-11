"""Root environment settings. Deployment variables take precedence."""
from dataclasses import dataclass
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]

@dataclass(frozen=True)
class Settings:
    database: Path
    operator_token: str = ""
    lease_seconds: int = 60
    heartbeat_seconds: int = 10
    poll_seconds: float = 1
    allowed_repositories: tuple[str, ...] = ()

    def __post_init__(self):
        if self.heartbeat_seconds <= 0 or self.lease_seconds <= 2 * self.heartbeat_seconds:
            raise ValueError("Lease must exceed twice the positive heartbeat interval")
        if self.poll_seconds <= 0:
            raise ValueError("Poll interval must be positive")

    @classmethod
    def load(cls):
        load_dotenv(ROOT / ".env", override=False)
        return cls(
            Path(os.getenv("TORQUE_DATABASE", str(ROOT / "var" / "torque.sqlite3"))).resolve(),
            os.getenv("TORQUE_OPERATOR_TOKEN", ""),
            int(os.getenv("TORQUE_LEASE_SECONDS", "60")),
            int(os.getenv("TORQUE_HEARTBEAT_SECONDS", "10")),
            float(os.getenv("TORQUE_POLL_SECONDS", "1")),
            tuple(x.strip().lower() for x in os.getenv("TORQUE_ALLOWED_REPOSITORIES", "").split(",") if x.strip()),
        )
