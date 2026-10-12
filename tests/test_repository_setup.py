import json
import time
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from backend.repository_configuration import SetupConfig
from backend.repository_setup import active_recipe, setup_record
from backend.models import TestResult as RemoteResult, Conflict
from test_github_auth import setup, seed

SHA = 'a' * 40
WORKFLOW_SHA = 'b' * 40
CONFIG = {'framework': 'pytest', 'test_files': ['tests/test_math.py'], 'editable_files': ['src/math.py']}
HEADERS = {'Origin': 'http://localhost:3000', 'X-CSRF-Token': 'csrf'}


class Runner:
    passed = True
    head = WORKFLOW_SHA
    def __init__(self, recipe):
        self.recipe = recipe
        self.repository = 'davre001/Torque'
        self.workflow = 'torque-remote-tests.yml'
        self.workflow_sha = WORKFLOW_SHA
    def preflight(self): pass
    def bind_source(self, *args): pass
    def dispatch(self, request_id, replacements):
        self.__class__.request_id = request_id
        assert replacements == {}
    def _request(self, *args, **kwargs):
        class Response:
            def json(self):
                return {'workflow_runs': [{'display_title': 'Torque test ' + Runner.request_id,
                        'status': 'completed', 'head_sha': Runner.head, 'id': 123}]}
        return Response()
    def _completed_result(self, *args):
        return RemoteResult(exit_code=0 if self.passed else 1, command=['pytest'], output='test_math PASSED' if self.passed else 'AssertionError: expected 10',
                          failure_kind=None if self.passed else 'assertion', assertions_passed=int(self.passed))
    def close(self): pass


def configured(tmp_path, monkeypatch):
    monkeypatch.setenv('TORQUE_RUNNER', 'github-actions')
    app = setup(tmp_path, monkeypatch)
    auth = app.state.github_auth
    def repositories(user):
        return [{'full_name': 'source/demo', 'permissions': {'push': True},
                 'app_permissions': {'contents': 'write', 'issues': 'read', 'pull_requests': 'write'}}]
    monkeypatch.setattr(auth, 'repositories', repositories)
    def api(token, path):
        if '/commits/' in path: return {'sha': SHA}
        if '/git/trees/' in path: return {'tree': [{'path': p, 'type': 'blob', 'mode': '100644', 'size': 20} for p in CONFIG['test_files'] + CONFIG['editable_files']]}
        return {'default_branch': 'main', 'private': False}
    monkeypatch.setattr(auth, 'api', api)
    monkeypatch.setattr('backend.tools.repository_runner.RepositoryRunner', Runner)
    monkeypatch.setattr(Runner, 'passed', True)
    monkeypatch.setattr(Runner, 'head', WORKFLOW_SHA)
    return app


@pytest.mark.parametrize('change', [
    {'editable_files': ['../secrets']}, {'test_files': ['/etc/passwd']},
    {'editable_files': ['.env']}, {'editable_files': ['tests/test_math.py']},
    {'editable_files': ['package.json']}, {'command': 'curl evil'},
    {'framework': 'npm'}, {'test_files': ['tests/test_math.py', 'tests/test_math.py']},
])
def test_config_rejects_unsafe_or_ambiguous_scope(change):
    with pytest.raises(ValidationError): SetupConfig.model_validate({**CONFIG, **change})


def test_validation_activation_and_user_isolation(tmp_path, monkeypatch):
    app = configured(tmp_path, monkeypatch)
    with TestClient(app) as client:
        seed(app, 'github:1', 'session1'); seed(app, 'github:2', 'session2')
        client.cookies.set('torque_session', 'session1')
        assert client.post('/api/repositories/source/demo/setup', json=CONFIG).status_code == 403
        response = client.post('/api/repositories/source/demo/setup', json=CONFIG, headers=HEADERS)
        assert response.status_code == 202
        assert response.json()['status'] == 'validating'
        assert active_recipe(app.state.store, 'github:1', 'source/demo') is None
        assert client.post('/api/repositories/source/demo/setup', json=CONFIG, headers=HEADERS).status_code == 409
        assert client.get('/api/repositories/source/demo/setup').json()['status'] == 'ready'
        recipe = active_recipe(app.state.store, 'github:1', 'source/demo')
        assert recipe.repository_setup['suite_sha'] == SHA
        assert recipe.editable_files == ['src/math.py']
        assert client.get('/api/auth/github/repositories').json()['repositories'][0]['run_supported']
        client.cookies.set('torque_session', 'session2')
        assert client.get('/api/repositories/source/demo/setup').json()['status'] == 'not_configured'
        assert active_recipe(app.state.store, 'github:2', 'source/demo') is None


def test_onboarded_repository_can_submit_without_deployment_allowlist(tmp_path, monkeypatch):
    from dataclasses import replace
    app = configured(tmp_path, monkeypatch)
    app.state.settings = replace(app.state.settings, allowed_repositories=())
    # create_app captures settings; construct with the empty policy from the outset.
    from backend.api import create_app
    empty = create_app(app.state.settings)
    monkeypatch.setattr(empty.state.github_auth, 'repositories', app.state.github_auth.repositories)
    monkeypatch.setattr(empty.state.github_auth, 'api', app.state.github_auth.api)
    with TestClient(empty) as client:
        seed(empty, 'github:1', 'session1'); client.cookies.set('torque_session', 'session1')
        issue = {'issue_url': 'https://github.com/source/demo/issues/4'}
        assert client.post('/api/runs', json=issue, headers=HEADERS).status_code == 422
        assert client.post('/api/repositories/source/demo/setup', json=CONFIG, headers=HEADERS).status_code == 202
        client.get('/api/repositories/source/demo/setup')
        assert client.post('/api/runs', json=issue, headers=HEADERS).status_code == 201
        assert client.post('/api/repositories/source/demo/setup', json=CONFIG, headers=HEADERS).status_code == 409


@pytest.mark.parametrize('tamper', ['failure', 'workflow'])
def test_failed_validation_never_activates(tmp_path, monkeypatch, tamper):
    app = configured(tmp_path, monkeypatch)
    with TestClient(app) as client:
        seed(app, 'github:1', 'session1'); client.cookies.set('torque_session', 'session1')
        assert client.post('/api/repositories/source/demo/setup', json=CONFIG, headers=HEADERS).status_code == 202
        if tamper == 'failure': monkeypatch.setattr(Runner, 'passed', False)
        else: monkeypatch.setattr(Runner, 'head', 'c' * 40)
        assert client.get('/api/repositories/source/demo/setup').json()['status'] == 'failed'
        assert active_recipe(app.state.store, 'github:1', 'source/demo') is None


def test_revoked_access_and_running_configuration_are_protected(tmp_path, monkeypatch):
    app = configured(tmp_path, monkeypatch)
    with TestClient(app) as client:
        seed(app, 'github:1', 'session1'); client.cookies.set('torque_session', 'session1')
        app.state.store.submit('https://github.com/source/demo/issues/1', 'github:1')
        assert client.post('/api/repositories/source/demo/setup', json=CONFIG, headers=HEADERS).status_code == 409
        monkeypatch.setattr(app.state.github_auth, 'repositories', lambda user: [])
        assert client.get('/api/repositories/source/demo/setup').status_code == 403


def test_setup_revision_fenced_at_run_admission(tmp_path, monkeypatch):
    app = configured(tmp_path, monkeypatch)
    with TestClient(app) as client:
        seed(app, 'github:1', 'session1'); client.cookies.set('torque_session', 'session1')
        client.post('/api/repositories/source/demo/setup', json=CONFIG, headers=HEADERS)
        client.get('/api/repositories/source/demo/setup')
        row = setup_record(app.state.store, 'github:1', 'source/demo')
        row['request_id'] = 'stale'
        with pytest.raises(Conflict):
            app.state.store.submit('https://github.com/source/demo/issues/2', 'github:1', repository_setup=row)


def test_migration_preserves_existing_runs(tmp_path):
    from backend.store import Store
    store = Store(tmp_path/'db')
    store.initialize()
    run = store.submit('https://github.com/source/demo/issues/1')
    with store.transaction() as db:
        db.execute('DELETE FROM schema_migrations WHERE version=2')
        db.execute('DROP TABLE repository_setups')
    store.initialize()
    assert store.get(run)['status'] == 'queued'
    with store.transaction() as db:
        assert db.execute('SELECT MAX(version) FROM schema_migrations').fetchone()[0] == 2
