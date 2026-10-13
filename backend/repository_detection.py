"""Conservative discovery for the existing managed repository test runner."""
import base64
import json
import re
from urllib.parse import quote
from fastapi import HTTPException
from pydantic import ValidationError
from backend.repository_configuration import SetupConfig


def validation_source(auth, user, repository, configuration):
    from backend.repository_scope import source_allowed
    token = auth.authorize(user, repository)
    root = '/repos/' + repository
    repo = auth.api(token, root)
    if repo.get('private') or repo.get('archived'):
        raise HTTPException(422, 'Choose an active public repository')
    sha = auth.api(token, root + '/commits/' + quote(repo['default_branch'], safe=''))['sha']
    tree = auth.api(token, root + '/git/trees/' + sha + '?recursive=1')
    if tree.get('truncated'):
        raise HTTPException(422, 'Repository tree exceeds supported investigation scope')
    source = sorted(p['path'] for p in tree.get('tree', []) if p.get('type') == 'blob' and p.get('mode') in {'100644', '100755'} and p.get('size', 0) <= 100000 and source_allowed(p['path'], configuration))
    if not source:
        raise HTTPException(422, 'No supported source files detected')
    return source[:10]


def detect_configuration(paths, package=None):
    paths = sorted(paths)
    npm = package is not None
    if npm and package.get('scripts', {}).get('test') not in {'vitest run', 'jest --runInBand', 'node --test'}:
        raise HTTPException(422, 'Test command needs manual setup; supported commands are vitest run, jest --runInBand and node --test')
    tests, source = [], []
    for path in paths:
        parts = path.split('/')
        name = parts[-1]
        if any(p.startswith('.') or p in {'node_modules', 'venv', '__pycache__', 'dist', 'build', 'coverage'} for p in parts):
            continue
        is_test = any(p.lower() in {'test', 'tests', '__tests__'} for p in parts) or bool(re.search(r'\.(test|spec)\.', name)) or name.startswith('test_') or name.endswith('_test.py')
        config = name in {'package.json', 'package-lock.json'} or name.startswith(('vitest.config.', 'jest.config.', 'vite.config.', 'tsconfig')) if npm else name in {'conftest.py', 'pytest.ini', 'pyproject.toml', 'requirements.txt'}
        supported = path.endswith(('.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs')) if npm else path.endswith('.py')
        if (is_test and supported) or config:
            tests.append(path)
        elif supported:
            source.append(path)
    if not any(p.endswith(('.py', '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs')) and ('test' in p.lower() or 'spec' in p.lower()) for p in tests):
        raise HTTPException(422, 'No supported tests detected; configure tests manually')
    try:
        # Choose a bounded frozen test subset automatically. Source paths here
        # only bootstrap validation; each issue gets its own investigated scope.
        configuration = [p for p in tests if p.rsplit('/', 1)[-1] in {'package.json', 'package-lock.json', 'conftest.py', 'pytest.ini', 'pyproject.toml', 'requirements.txt'} or p.rsplit('/', 1)[-1].startswith(('vitest.config.', 'jest.config.', 'vite.config.', 'tsconfig'))]
        cases = [p for p in tests if p not in configuration]
        if len(configuration) >= 10:
            raise ValueError('Configuration exceeds scope')
        selected_tests = configuration + cases[:10-len(configuration)]
        return SetupConfig(framework='npm' if npm else 'pytest', test_files=selected_tests, editable_files=source[:10])
    except (ValidationError, ValueError):
        raise HTTPException(422, 'Test configuration could not be detected automatically') from None


def detect_repository(auth, user, repository):
    token = auth.authorize(user, repository)
    root = '/repos/' + repository
    repo = auth.api(token, root)
    if repo.get('private') or repo.get('archived'):
        raise HTTPException(422, 'Automatic tests require an active public repository')
    sha = auth.api(token, root + '/commits/' + quote(repo['default_branch'], safe=''))['sha']
    tree = auth.api(token, root + '/git/trees/' + sha + '?recursive=1')
    if tree.get('truncated'):
        raise HTTPException(422, 'Repository needs manual test setup; tree exceeds supported scope')
    entries = {p['path']: p for p in tree.get('tree', []) if p.get('type') == 'blob'}
    package = None
    if 'package.json' in entries:
        if entries['package.json'].get('size', 0) > 100000:
            raise HTTPException(422, 'Package manifest exceeds supported size')
        payload = auth.api(token, root + '/contents/package.json?ref=' + sha)
        try:
            package = json.loads(base64.b64decode(payload['content']))
            if not isinstance(package, dict) or not isinstance(package.get('scripts', {}), dict):
                raise ValueError()
        except (KeyError, ValueError, TypeError):
            raise HTTPException(422, 'Package manifest could not be detected; use manual setup') from None
    return detect_configuration(entries, package)
