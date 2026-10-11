from types import SimpleNamespace
from backend.integrations.gemini import Gemini
from backend.integrations.providers import Budget, StructuredProvider
from backend.execution import Limits
from backend.models import Review


def test_gemini_receives_strict_schema_and_retains_usage():
    calls=[]
    def generate(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(text='{"approved":true,"rationale":"passed","satisfied_criteria":[0]}',
                               usage_metadata=SimpleNamespace(prompt_token_count=10,candidates_token_count=15,thoughts_token_count=5))
    adapter=Gemini.__new__(Gemini)
    adapter.model='fixture-model'
    adapter.client=SimpleNamespace(models=SimpleNamespace(generate_content=generate))
    budget=Budget(Limits())
    result=StructuredProvider(adapter,budget,0,0,lambda:None).ask('review',{},Review)
    assert result.approved
    assert calls[0]['config'].response_json_schema==Review.model_json_schema()
    assert calls[0]['config'].response_json_schema['additionalProperties'] is False
    assert budget.tokens==30
