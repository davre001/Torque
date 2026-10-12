"""User-scoped repository onboarding; activation requires a hosted test result."""
import json
import os
import re
import time
import uuid
from urllib.parse import quote
from fastapi import HTTPException
from backend.repository_configuration import SetupConfig
from backend.execution import Recipe
from backend.models import PipelineError



def setup_record(store, user, repository):
    with store.transaction() as db:
        row = db.execute('SELECT * FROM repository_setups WHERE user_id=? AND repository=?',
                         (user, repository.lower())).fetchone()
    return dict(row) if row else None


def setup_recipe(row):
    config = SetupConfig.model_validate_json(row['config'])
    return Recipe(image='remote-managed', command=['managed-repository-tests'],
                  context_files=list(dict.fromkeys(config.editable_files + config.test_files)),
                  editable_files=config.editable_files,
                  acceptance_criteria=['The frozen repository test suite passes.'],
                  suite_directory='remote-managed', require_baseline_failure=False,
                  repository_setup={**config.model_dump(), 'suite_sha': row['source_sha']})


def active_recipe(store, user, repository):
    row = setup_record(store, user, repository)
    if row and row['status'] == 'ready':
        return setup_recipe(row)
    return None


def public_setup(row):
    if not row:
        return {'status': 'not_configured'}
    return {'status': row['status'], 'source_sha': row['source_sha'],
            'configuration': json.loads(row['config']), 'result': json.loads(row['result'])}


def start_setup(store, auth, user, repository, config):
    if os.getenv('TORQUE_RUNNER', 'docker') != 'github-actions':
        raise HTTPException(503, 'Automatic repository setup requires the GitHub Actions test runner')
    repository = repository.lower()
    token = auth.authorize(user, repository)
    repo = auth.api(token, '/repos/' + repository)
    if repo.get('private') or repo.get('archived'):
        raise HTTPException(422, 'Choose an active public repository')
    sha = auth.api(token, '/repos/' + repository + '/commits/' + quote(repo['default_branch'], safe=''))['sha']
    if not re.fullmatch('[a-f0-9]{40}', sha):
        raise HTTPException(502, 'GitHub returned an invalid revision')
    # Check explicit file scope at the pinned commit before dispatching anything.
    tree = auth.api(token, '/repos/' + repository + '/git/trees/' + sha + '?recursive=1')
    if tree.get('truncated'):
        raise HTTPException(422, 'Repository tree exceeds supported validation scope')
    entries = {item['path']: item for item in tree.get('tree', [])}
    total = 0
    for path in config.test_files + config.editable_files:
        item = entries.get(path, {})
        if item.get('type') != 'blob' or item.get('mode') not in {'100644', '100755'} or item.get('size', 0) > 100000:
            raise HTTPException(422, 'Choose regular files smaller than 100 KB: ' + path)
        total += item.get('size', 0)
    if total > 250000:
        raise HTTPException(422, 'Selected files exceed the 250 KB limit')
    from backend.tools.repository_runner import RepositoryRunner
    request_id = uuid.uuid4().hex
    row = {'config': config.model_dump_json(), 'source_sha': sha}
    runner = RepositoryRunner(setup_recipe(row))
    try:
        runner.preflight()
        runner.bind_source(*repository.split('/'), sha)
        now = time.time()
        with store.transaction() as db:
            prefix = 'https://github.com/' + repository + '/issues/'
            if db.execute("SELECT 1 FROM runs WHERE user_id=? AND SUBSTR(LOWER(issue_url),1,?)=? AND status NOT IN ('completed','failed','cancelled','interrupted')", (user, len(prefix), prefix)).fetchone():
                raise HTTPException(409, 'Finish or cancel existing repository runs before changing tests')
            if db.execute("SELECT COUNT(*) FROM repository_setups WHERE status='validating' AND created_at>?", (now - 900,)).fetchone()[0] >= 3:
                raise HTTPException(429, 'Validation capacity reached; try again later')
            previous = db.execute('SELECT status,created_at,validation_day,validation_count FROM repository_setups WHERE user_id=? AND repository=?', (user, repository)).fetchone()
            if previous and (previous['status'] == 'validating' and now - previous['created_at'] < 900 or now - previous['created_at'] < 60):
                raise HTTPException(409, 'Validation already started; refresh its status')
            count = db.execute('SELECT COUNT(*) FROM repository_setups WHERE user_id=?', (user,)).fetchone()[0]
            if not previous and count >= 10:
                raise HTTPException(429, 'Repository setup limit reached')
            day = int(now // 86400)
            attempts = previous['validation_count'] if previous and previous['validation_day'] == day else 0
            if attempts >= 3:
                raise HTTPException(429, 'Daily repository validation limit reached; try tomorrow')
            db.execute('''INSERT INTO repository_setups VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(user_id,repository) DO UPDATE SET request_id=excluded.request_id,
                status=excluded.status,config=excluded.config,source_sha=excluded.source_sha,
                workflow_sha=excluded.workflow_sha,created_at=excluded.created_at,
                updated_at=excluded.updated_at,result=excluded.result,
                validation_day=excluded.validation_day,validation_count=excluded.validation_count''',
                (user, repository, request_id, 'validating', row['config'], sha, runner.workflow_sha, now, now, '{}', day, attempts + 1))
        try:
            runner.dispatch(request_id, {})
        except PipelineError:
            with store.transaction() as db:
                db.execute("UPDATE repository_setups SET status='failed',result=? WHERE user_id=? AND repository=? AND request_id=?",
                           (json.dumps({'message': 'Test dispatch failed; retry validation'}), user, repository, request_id))
            raise
    finally:
        runner.close()
    return public_setup(setup_record(store, user, repository))


def refresh_setup(store, auth, user, repository):
    repository = repository.lower()
    auth.authorize(user, repository)
    row = setup_record(store, user, repository)
    if not row or row['status'] != 'validating':
        return public_setup(row)
    from backend.tools.repository_runner import RepositoryRunner
    runner = RepositoryRunner(setup_recipe(row))
    runner.workflow_sha = row['workflow_sha']
    runner.bind_source(*repository.split('/'), row['source_sha'])
    result = None
    try:
        runs = runner._request('GET', f'/repos/{runner.repository}/actions/workflows/{runner.workflow}/runs',
                               params={'event': 'workflow_dispatch', 'per_page': 100}).json()['workflow_runs']
        run = next((r for r in runs if r['display_title'] == 'Torque test ' + row['request_id']), None)
        if run and run['status'] == 'completed':
            if run['head_sha'] != row['workflow_sha']:
                raise PipelineError('Validation workflow revision changed')
            result = runner._completed_result(run, row['request_id'], lambda: None)
        elif time.time() - row['created_at'] > 900:
            raise PipelineError('Validation timed out; retry setup')
    except PipelineError as exc:
        state, payload = 'failed', {'message': str(exc)}
    else:
        if result is None:
            return public_setup(row)
        state = 'ready' if result.passed and result.assertions_passed == 1 else 'failed'
        payload = {'message': 'Tests passed; repository enabled' if state == 'ready' else 'Tests failed; fix the test setup and retry',
                   'output': result.output[-12000:], 'exit_code': result.exit_code}
    finally:
        runner.close()
    with store.transaction() as db:
        db.execute('UPDATE repository_setups SET status=?,result=?,updated_at=? WHERE user_id=? AND repository=? AND request_id=?',
                   (state, json.dumps(payload), time.time(), user, repository, row['request_id']))
    return public_setup(setup_record(store, user, repository))
