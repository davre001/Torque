import pytest
from backend.repository_scope import select_source, source_allowed
from backend.repository_setup import setup_recipe
from backend.models import Plan, PipelineError
import json

CONFIG = {'framework':'pytest', 'test_files':['tests/test_math.py'], 'editable_files':['old.py']}


def test_investigator_can_choose_source_outside_validation_bootstrap(tmp_path):
    (tmp_path/'old.py').write_text('old = 1')
    (tmp_path/'actual_fix.py').write_text('value = 2')
    (tmp_path/'tests').mkdir()
    (tmp_path/'tests/test_math.py').write_text('assert True')
    recipe = setup_recipe({'config':json.dumps(CONFIG), 'source_sha':'a'*40})
    class Provider:
        def ask(self, prompt, payload, model):
            assert payload['source_files'] == ['actual_fix.py', 'old.py']
            return Plan(summary='Investigate the reported bug', files=['actual_fix.py'], acceptance_criteria=recipe.acceptance_criteria)
    assert select_source(tmp_path, {'title':'Fix value'}, recipe, Provider(), lambda:None) == ['actual_fix.py']
    assert recipe.context_files == recipe.editable_files == ['actual_fix.py']


@pytest.mark.parametrize('name', ['.env', 'tests/test_math.py', 'package.json', '../secret.py', 'node_modules/a.js', 'pyproject.toml', 'dist/a.js'])
def test_discovery_excludes_protected_paths(name):
    assert not source_allowed(name, CONFIG)


def test_model_cannot_choose_file_outside_inventory(tmp_path):
    (tmp_path/'old.py').write_text('old = 1')
    recipe = setup_recipe({'config':json.dumps(CONFIG), 'source_sha':'a'*40})
    class Provider:
        def ask(self, *args):
            return Plan(summary='bad scope', files=['unknown.py'], acceptance_criteria=recipe.acceptance_criteria)
    with pytest.raises(PipelineError):
        select_source(tmp_path, {}, recipe, Provider(), lambda:None)
