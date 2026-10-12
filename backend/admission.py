"""Conservative UTC-day reservations, retained after failures and cancellation."""
from dataclasses import dataclass
import math
import os
from backend.execution import Limits

@dataclass(frozen=True)
class Admission:
    queue: int = 20
    per_user_active: int = 1
    per_user_daily: int = 5
    per_user_usd: float = 10
    global_usd: float = 20
    reserve_usd: float = 2

    def __post_init__(self):
        if any(type(v) is not int or v <= 0 for v in (self.queue,self.per_user_active,self.per_user_daily)):
            raise ValueError('Admission counts must be positive integers')
        if any(not math.isfinite(v) or v <= 0 for v in (self.per_user_usd,self.global_usd,self.reserve_usd)):
            raise ValueError('Admission spending limits must be positive and finite')

    @classmethod
    def load(cls):
        return cls(int(os.getenv('TORQUE_MAX_ACTIVE_RUNS','20')),
                   int(os.getenv('TORQUE_USER_ACTIVE_RUNS','1')),
                   int(os.getenv('TORQUE_USER_DAILY_RUNS','5')),
                   float(os.getenv('TORQUE_USER_DAILY_USD','10')),
                   float(os.getenv('TORQUE_DEPLOYMENT_DAILY_USD','20')),
                   Limits.load().max_cost_usd)
