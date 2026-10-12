from fastapi.testclient import TestClient
from backend.repository_policy import eligibility
from test_github_auth import setup, seed


def test_eligibility_requires_both_allowlist_and_recipe():
    assert not eligibility('source/demo', (), {'source/demo': object()})['run_supported']
    assert not eligibility('source/demo', ('source/demo',), {})['run_supported']
    assert not eligibility('source/demo', ('source/demo',), None)['run_supported']
    assert eligibility('Source/Demo', ('source/demo',), {'source/demo': object()})['run_supported']
    assert eligibility('source/demo', None, {'source/demo': object()})['run_supported']
    assert not eligibility('source/demo', None, {})['run_supported']


def test_github_user_can_use_reviewed_repository_without_operator_allowlist(tmp_path, monkeypatch):
    from backend.api import create_app
    from backend.config import Settings
    setup(tmp_path, monkeypatch)
    app = create_app(Settings(tmp_path/'separate-db', allowed_repositories=()))
    auth = app.state.github_auth
    monkeypatch.setattr(auth, 'repositories', lambda user: [
        {'full_name': 'source/demo', 'permissions': {}, 'app_permissions': {'contents':'read','issues':'read'}}])
    monkeypatch.setattr('backend.repository_policy.reviewed_recipes', lambda: {'source/demo': object()})
    with TestClient(app) as client:
        seed(app, 'github:1', 'session1')
        client.cookies.set('torque_session', 'session1')
        headers = {'Origin':'http://localhost:3000','X-CSRF-Token':'csrf'}
        assert client.get('/api/auth/github/repositories').json()['repositories'][0]['run_supported']
        assert client.post('/api/runs',json={'issue_url':'https://github.com/source/demo/issues/4'},headers=headers).status_code == 201
        # A configured recipe cannot confer access to another user's repository.
        monkeypatch.setattr(auth, 'repositories', lambda user: [])
        assert client.post('/api/runs',json={'issue_url':'https://github.com/source/demo/issues/5'},headers=headers).status_code == 403


def test_browser_unsupported_submission_never_queues(tmp_path, monkeypatch):
    app = setup(tmp_path, monkeypatch)
    monkeypatch.setattr('backend.repository_policy.reviewed_recipes', lambda: {})
    monkeypatch.setattr(app.state.github_auth, 'repositories', lambda user: [
        {'full_name': 'source/demo', 'permissions': {}, 'app_permissions': {'contents': 'read', 'issues': 'read'}}
    ])
    with TestClient(app) as client:
        seed(app, 'github:1', 'session1')
        client.cookies.set('torque_session', 'session1')
        repo = client.get('/api/auth/github/repositories').json()['repositories'][0]
        assert not repo['run_supported']
        response = client.post('/api/runs', json={'issue_url': 'https://github.com/source/demo/issues/4'},
                               headers={'Origin': 'http://localhost:3000', 'X-CSRF-Token': 'csrf'})
        assert response.status_code == 422
        assert client.get('/api/runs').json()['runs'] == []
        monkeypatch.setattr('backend.repository_policy.reviewed_recipes', lambda: {'source/demo': object()})
        assert client.get('/api/auth/github/repositories').json()['repositories'][0]['run_supported']
        assert client.post('/api/runs', json={'issue_url': 'https://github.com/source/demo/issues/4'},
                           headers={'Origin': 'http://localhost:3000', 'X-CSRF-Token': 'csrf'}).status_code == 201
