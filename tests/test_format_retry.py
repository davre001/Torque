import pytest
from backend.execution import Limits
from backend.integrations.providers import Budget, Response, StructuredProvider
from backend.models import Plan, PipelineError, BudgetExceeded


class Adapter:
    model = 'fixture-model'
    def __init__(self, outputs):
        self.outputs = iter(outputs)
        self.prompts = []
    def complete(self, prompt, maximum):
        self.prompts.append(prompt)
        return Response(next(self.outputs), 10, 10, self.model)


def test_format_retry_charges_both_calls_and_does_not_echo_bad_output():
    adapter = Adapter(['private malformed output', '{"summary":"fix","acceptance_criteria":["test"],"files":["a.py"]}'])
    budget = Budget(Limits())
    result = StructuredProvider(adapter, budget, 3, 15, lambda: None, 0).ask('plan', {}, Plan)
    assert result.files == ['a.py']
    assert budget.calls == 2 and budget.tokens == 40
    assert len(budget.records) == 2
    assert budget.estimated_cost == pytest.approx(0.00036)
    assert 'private malformed output' not in adapter.prompts[1]


def test_format_retry_remains_strict_and_bounded():
    adapter = Adapter(['broken', '{"summary":"fix","acceptance_criteria":["test"],"files":["a.py"],"extra":"ignored?"}'])
    budget = Budget(Limits())
    with pytest.raises(PipelineError, match='extra_forbidden'):
        StructuredProvider(adapter, budget, 0, 0, lambda: None, 0).ask('plan', {}, Plan)
    assert budget.calls == 2


def test_format_retry_cannot_override_budget():
    adapter = Adapter(['broken'])
    budget = Budget(Limits(max_calls=1))
    with pytest.raises(BudgetExceeded):
        StructuredProvider(adapter, budget, 0, 0, lambda: None, 0).ask('plan', {}, Plan)
    assert len(adapter.prompts) == 1
