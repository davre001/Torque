import pytest
from backend.execution import Limits
from backend.integrations.providers import Budget, StructuredProvider
from backend.models import Cancelled, Recovery


@pytest.mark.parametrize('interruption', [Cancelled, InterruptedError])
def test_blocked_request_error_preserves_shutdown_and_reservation(interruption):
    class Adapter:
        model = 'fixture'
        calls = 0
        def complete(self, *_):
            self.calls += 1
            raise TimeoutError('request timed out')
    adapter = Adapter()
    budget = Budget(Limits())
    checks = []
    def checkpoint():
        checks.append(1)
        if len(checks) > 1: raise interruption('stop requested')
    provider = StructuredProvider(adapter, budget, 3, 15, checkpoint, transport_retries=1)
    with pytest.raises(interruption): provider.ask('fixture', {}, Recovery)
    assert adapter.calls == 1
    assert budget.calls == 1 and budget.estimated_cost > 0
    assert budget.records[0]['usage'] == 'request-failed-reserved'
