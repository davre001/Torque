from backend.agents.recovery import recover
from backend.models import Plan, Patch, Recovery


def test_recovery_gets_actual_patch_and_boundary_observation():
    class Provider:
        def ask(self, instruction, data, schema):
            assert 'not the index' in instruction
            assert 'do not infer missing code' in instruction
            assert data['hosted_trace']['trace_id'] == 'a' * 32
            assert data['failure']['tests']['output'].endswith('expected split=0; actual split=45')
            assert data['attempted_patch']['edits'][0]['replacements'][0]['replacement'].endswith('});')
            assert schema is Recovery
            return Recovery(strategy='Preserve zero rather than treating it as absent')

    patch = Patch(summary='Keyboard handler', edits=[{
        'path': 'site/index.html', 'original_sha256': 'b' * 64,
        'replacements': [{'search': 'old handler', 'replacement':
                          'cmp.addEventListener("keydown", () => { readValue() || 50; });'}]}])
    plan = Plan(summary='Accessible slider', acceptance_criteria=['Keyboard boundaries'],
                files=['site/index.html'])
    result = recover(Provider(), plan, {'tests': {'assertions_passed': 4,
                     'output': 'slider-keys: expected split=0; actual split=45'}},
                     {'site/index.html': {'content': 'source', 'sha256': 'b' * 64}},
                     hosted={'trace_id': 'a' * 32}, patch=patch)
    assert 'Preserve zero' in result
