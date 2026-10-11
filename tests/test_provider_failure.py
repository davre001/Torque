import pytest
from backend.execution import Limits
from backend.integrations.providers import Budget, StructuredProvider
from backend.models import Plan, BudgetExceeded


def test_retry_budget_preserves_provider_failure_and_unknown_usage():
    class Failure(Exception):
        code = 503
    class Adapter:
        model = "fixture-model"
        calls = 0
        def complete(self,*args):
            self.calls += 1
            raise Failure("private key and provider payload must not escape")
    adapter = Adapter()
    budget = Budget(Limits(max_tokens=10000))
    provider = StructuredProvider(adapter,budget,0,0,lambda:None)
    with pytest.raises(BudgetExceeded,match="HTTP 503.*retry blocked") as caught:
        provider.ask("Investigate",{},Plan)
    assert adapter.calls == 1
    assert budget.records[0]["usage"] == "request-failed-reserved"
    assert budget.records[0]["http_status"] == 503
    assert "private key" not in str(caught.value)
