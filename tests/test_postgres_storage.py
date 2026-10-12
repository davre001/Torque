"""Opt-in integration checks against disposable, isolated PostgreSQL schemas."""
import concurrent.futures
import os
import uuid
from urllib.parse import parse_qsl,urlencode,urlsplit,urlunsplit
import pytest
from backend.store import Store
from backend.admission import Admission
from backend.models import AdmissionDenied, LeaseLost, Status
from backend.github_auth import GitHubAuth

pytestmark = pytest.mark.skipif(not os.getenv('TORQUE_TEST_DATABASE_URL'),reason='No test PostgreSQL configured')


@pytest.fixture
def pg_store():
    import psycopg
    dsn=os.environ['TORQUE_TEST_DATABASE_URL']
    schema='torque_test_'+uuid.uuid4().hex
    with psycopg.connect(dsn,autocommit=True) as db:
        db.execute(f'CREATE SCHEMA {schema}')
    url=urlsplit(dsn)
    options=dict(parse_qsl(url.query));options['options']='-csearch_path='+schema
    store=Store(urlunsplit(url._replace(query=urlencode(options))))
    try:
        store.initialize(migrate=True);store.initialize();GitHubAuth(store).initialize()
        yield store
    finally:
        with psycopg.connect(dsn,autocommit=True) as db:
            db.execute(f'DROP SCHEMA {schema} CASCADE')


def test_postgres_concurrent_admission_claim_cancel_and_expiry(pg_store):
    store=pg_store
    def submit(_):
        try:return store.submit('https://github.com/source/demo/issues/1',admission=Admission.load())
        except AdmissionDenied:return None
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        runs=list(pool.map(submit,range(6)))
    assert sum(bool(r) for r in runs)==1
    run=next(r for r in runs if r)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        claims=list(pool.map(lambda _:store.claim(60,run),range(6)))
    assert sum(bool(r) for r in claims)==1
    _,owner=next(r for r in claims if r)
    store.cancel(run,'operator')
    assert store.get(run)['cancel_requested']
    store.clock=lambda:__import__('time').time()+100
    assert store.claim(60,run) is None
    assert store.get(run)['status']=='interrupted'
    with pytest.raises(LeaseLost):store.heartbeat(run,owner,60)


def test_postgres_artifacts_auth_counters_and_publication_fencing(pg_store):
    from backend.artifacts import Artifacts,read_durable
    store=pg_store;run=store.submit('https://github.com/source/demo/issues/1')
    with store.transaction() as db:
        db.execute('INSERT INTO http_admission VALUES(?,?,1) ON CONFLICT(window,actor) DO UPDATE SET count=count+1',(1,'actor'))
        db.execute('INSERT INTO http_admission VALUES(?,?,1) ON CONFLICT(window,actor) DO UPDATE SET count=count+1',(1,'actor'))
        assert db.execute('SELECT count FROM http_admission').fetchone()[0]==2
        db.execute('INSERT INTO oauth_states VALUES(?,?,?)',('hash','verifier',1234))
        assert db.execute('SELECT verifier FROM oauth_states').fetchone()['verifier']=='verifier'
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as root:
        entry=Artifacts(Path(root)/run,store=store).write('plan',{'summary':'demo'})
    assert read_durable(store,run,entry)=={'summary':'demo'}
    _,owner=store.claim(60,run)
    store.update(run,owner,Status.READY,result={'verified':True})
    publisher=store.claim_publication(run,'operator','source/demo')
    from backend.models import Conflict
    with pytest.raises(Conflict):store.claim_publication(run,'operator','source/demo')
    store.finish_publication(run,publisher,pr_url='https://github.com/source/demo/pull/1',commit_sha='a'*40)
    assert store.get(run)['status']=='completed'


def test_postgres_encrypted_restore_with_run_history(pg_store,tmp_path,monkeypatch):
    from cryptography.fernet import Fernet
    from backend import database_backup as backup
    store=pg_store
    run=store.submit('https://github.com/source/demo/issues/1')
    _,owner=store.claim(60,run)
    store.update(run,owner,Status.FAILED,result={'summary':'fixture history'})
    monkeypatch.setenv('TORQUE_SESSION_ENCRYPTION_KEY',Fernet.generate_key().decode())
    monkeypatch.setattr(backup,'ROOT',tmp_path)
    raw=backup.snapshot(store)
    path=backup.save(raw,'postgres')
    assert b'fixture history' not in path.read_bytes()
    report=backup.restore_check(path,os.environ['TORQUE_TEST_DATABASE_URL'])
    assert report['isolated_restore_passed'] and report['rows_verified']>=6


def test_postgres_artifact_limits_integrity_publication_and_retention(pg_store,tmp_path):
    import hashlib
    from types import SimpleNamespace
    from backend.artifacts import Artifacts,read_durable
    from backend.models import PipelineError
    from backend.publication import verified_files
    from backend.retention import cleanup
    store=pg_store
    run=store.submit('https://github.com/source/demo/issues/1')
    artifacts=Artifacts(tmp_path/run,('fixture-private-secret',),store)
    entry=artifacts.write('plan',{'summary':'fixture-private-secret'})
    assert artifacts.write('plan',{'summary':'fixture-private-secret'})==entry
    assert read_durable(store,run,entry)=={'summary':'[redacted]'}
    with pytest.raises(PipelineError,match='immutable'):
        artifacts.write('plan',{'summary':'changed'})
    with pytest.raises(PipelineError,match='2 MiB'):
        artifacts.write('oversize',{'content':'x'*(2*1024*1024)})
    # Four nearly full records fit; a fifth exceeds the independent run cap.
    for n in range(4):artifacts.write('large-'+str(n),{'content':'x'*(2*1024*1024-100)})
    with pytest.raises(PipelineError,match='8 MiB'):
        artifacts.write('large-4',{'content':'x'*1024})
    with store.transaction() as db:
        db.execute('UPDATE artifact_records SET content=? WHERE run_id=? AND name=?',('{}',run,'plan.json'))
    with pytest.raises(PipelineError,match='integrity'):
        read_durable(store,run,entry)

    ready=store.submit('https://github.com/source/demo/issues/2')
    writer=Artifacts(tmp_path/ready,store=store)
    entries=[writer.write('patch-1',{'summary':'Fix','edits':[{'path':'index.html','original_sha256':'0'*64,'content':'fixed\n'}]}),
             writer.write('tests-1',{'exit_code':0,'failure_kind':None,'timed_out':False,'assertions_passed':1}),
             writer.write('verified-context',{'index.html':{'content':'fixed\n'}})]
    for path in writer.root.iterdir():path.unlink()
    writer.root.rmdir()
    digest=hashlib.sha256(b'index.html\0fixed\n').hexdigest()
    verified={'run_id':ready,'result':{'verified':True,'artifacts':entries,'plan':{'acceptance_criteria':['works']},
              'patch_sha256':digest,'verified_content_sha256':digest},
              'attempts':[{'number':1,'tests_passed':True,'patch_sha256':digest,
                           'review':{'approved':True,'satisfied_criteria':[0]}}]}
    recipe=SimpleNamespace(acceptance_criteria=['works'],context_files=['index.html'],editable_files=['index.html'])
    assert verified_files(verified,recipe,store=store)=={'index.html':'fixed\n'}
    with store.transaction() as db:
        for identity,state in [(run,'failed'),(ready,'ready_to_publish')]:
            db.execute('UPDATE runs SET status=?,updated_at=0 WHERE run_id=?',(state,identity))
            db.execute("UPDATE jobs SET state='done' WHERE run_id=?",(identity,))
    report=cleanup(store,tmp_path,apply=True)
    assert any(item['run_id']==run and item.get('durable_artifacts')==5 for item in report['runs'])
    with store.transaction() as db:
        assert db.execute('SELECT COUNT(*) FROM artifact_records WHERE run_id=?',(run,)).fetchone()[0]==0
        assert db.execute('SELECT COUNT(*) FROM artifact_records WHERE run_id=?',(ready,)).fetchone()[0]==3
    assert verified_files(verified,recipe,store=store)=={'index.html':'fixed\n'}
