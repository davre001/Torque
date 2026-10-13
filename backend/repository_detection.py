"""Conservative discovery for the existing managed repository test runner."""
import base64
import json
import re
from urllib.parse import quote
from fastapi import HTTPException
from pydantic import ValidationError
from backend.repository_configuration import SetupConfig


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
        config = name in {'package.json', 'package-lock.json'} or name.startswith(('vitest.config.', 'jest.config.', 'vite.config.', 'tsconfig')) if npm else name in {'conftest.py', 'pytest.ini', 'pyproject.toml'}
        supported = path.endswith(('.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs')) if npm else path.endswith('.py')
        if is_test or config:
            tests.append(path)
        elif supported:
            source.append(path)
    if not any(p.endswith(('.py', '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs')) and ('test' in p.lower() or 'spec' in p.lower()) for p in tests):
        raise HTTPException(422, 'No supported tests detected; configure tests manually')
    try:
        return SetupConfig(framework='npm' if npm else 'pytest', test_files=tests, editable_files=source)
    except ValidationError:
        raise HTTPException(422, 'Detected file scope needs manual setup (up to 10 test files and 10 source files)') from None


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
