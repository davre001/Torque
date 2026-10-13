from fastapi.testclient import TestClient
from test_github_auth import setup, seed


def test_progress_reconciles_only_owned_queued_runs(tmp_path, monkeypatch):
    app = setup(tmp_path, monkeypatch)
    dispatched = []

    class Dispatcher:
        def __init__(self, store): pass
        def dispatch(self, run_id): dispatched.append(run_id)
        def close(self): pass

    monkeypatch.setattr('backend.dispatch.Dispatcher', Dispatcher)
    with TestClient(app) as client:
        seed(app, 'github:1', 'session1')
        seed(app, 'github:2', 'session2')
        monkeypatch.setenv('TORQUE_WORKER_DISPATCH', 'github-actions')
        client.cookies.set('torque_session', 'session1')
        own = app.state.store.submit('https://github.com/source/demo/issues/7', 'github:1')
        other = app.state.store.submit('https://github.com/source/demo/issues/8', 'github:2')
        assert client.get('/api/runs/' + other).status_code == 404
        assert not dispatched
        assert client.get('/api/runs/' + own).status_code == 200
        assert dispatched == [own]
        app.state.store.cancel(own, 'github:1')
        assert client.get('/api/runs/' + own).status_code == 200
        assert dispatched == [own]
