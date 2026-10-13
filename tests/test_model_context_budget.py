import hashlib
import json
import pytest
from backend.tools.files import bounded_source_context
from backend.integrations.providers import Budget
from backend.execution import Limits
from backend.models import BudgetExceeded


def test_large_source_context_fits_existing_token_reservation_and_preserves_hashes():
    content = 'unrelated = 1\n' * 500 + 'def signin_token():\n    return missing_token\n' + 'unrelated = 2\n' * 50
    original = {'content':content, 'sha256':hashlib.sha256(content.encode()).hexdigest()}
    context = {f'src/file{i}.py':dict(original) for i in range(10)}
    prompt = json.dumps({'context':context})
    with pytest.raises(BudgetExceeded, match='Token reservation'):
        Budget(Limits()).reserve(prompt, 3, 15)
    selected = bounded_source_context(context, 'signin token missing')
    assert sum(len(r['content'].encode()) for r in selected.values()) <= 12000
    assert all('def signin_token()' in r['content'] for r in selected.values())
    assert all(r['sha256'] == original['sha256'] and r['is_excerpt'] for r in selected.values())
    assert all(r['content'] == content for r in context.values())
    Budget(Limits()).reserve(json.dumps({'context':selected}), 3, 15)


@pytest.mark.parametrize('limits, calls, message', [
    (Limits(max_calls=1), 1, 'Model call budget'),
    (Limits(max_tokens=10), 0, 'Token reservation budget'),
    (Limits(max_cost_usd=.00001), 0, 'Estimated dollar reservation budget'),
])
def test_budget_denial_identifies_specific_limit_without_reserving_request(limits, calls, message):
    budget = Budget(limits)
    budget.calls = calls
    with pytest.raises(BudgetExceeded, match=message):
        budget.reserve('fixture', 3, 15)
    assert budget.calls == calls
    assert budget.tokens == 0
    assert budget.estimated_cost == 0
