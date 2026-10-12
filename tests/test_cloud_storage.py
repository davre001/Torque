import concurrent.futures
import json
from types import SimpleNamespace
import httpx
import pytest
from backend.database import Database, Row, postgres_sql
from backend.store import Store
from backend.admission import Admission
from backend.models import AdmissionDenied, Conflict, Status
from backend.artifacts import Artifacts, read_durable
from backend.dispatch import Dispatcher

URL = 'https://github.com/source/demo/issues/1'


def test_database_dsn_validation_and_row_compatibility():
    with pytest.raises(ValueError,match='TLS|sslmode'):
        Database('postgresql://user:private@remote.example/db')
    row = Row([('id',3),('name','demo')])
    assert dict(row) == {'id':3,'name':'demo'}
    assert tuple(row) == (3,'demo') and row[0] == row['id']
    assert 'ON CONFLICT DO NOTHING' in postgres_sql('INSERT OR IGNORE INTO users VALUES(?,?)')


def test_targeted_claim_never_takes_another_job(tmp_path):
    store=Store(tmp_path/'db');store.initialize()
    first, second = store.submit(URL), store.submit(URL)
    assert store.claim(60,'f'*32) is None
    _,owner=store.claim(60,second)
    store.update(second,owner,Status.FAILED)
    assert store.claim(60,second) is None
    assert store.claim(60,first)[0] == first


def test_uncertain_dispatch_reconciles_and_does_not_reserve_twice(tmp_path,monkeypatch):
    store=Store(tmp_path/'db');store.initialize();now=[1000];store.clock=lambda:now[0]
    run=store.submit(URL,idempotency_key='same',admission=Admission.load())
    monkeypatch.setenv('TORQUE_ACTIONS_TOKEN','fixture-token')
    posts=[]
    def handler(request):
        if request.method=='GET': return httpx.Response(200,json={'workflow_runs':[]})
        posts.append(json.loads(request.content));raise httpx.ReadTimeout('fixture')
    dispatch=Dispatcher(store,httpx.Client(base_url='https://api.github.com',transport=httpx.MockTransport(handler)))
    assert not dispatch.dispatch(run)
    assert not dispatch.dispatch(run)  # Backoff after ambiguous request.
    now[0]+=61
    assert not dispatch.dispatch(run)
    assert posts[0]['inputs']==posts[1]['inputs']
    assert store.submit(URL,idempotency_key='same',admission=Admission.load()) == run
    with store.transaction() as db:
        assert db.execute('SELECT COUNT(*) FROM admission_reservations').fetchone()[0] == 1
    claim=store.claim(60,run);assert claim and store.claim(60,run) is None


def test_durable_artifact_survives_local_deletion_and_detects_tampering(tmp_path):
    local=Store(tmp_path/'db');local.initialize();run=local.submit(URL)
    # Exercise the database artifact contract with SQLite; real PostgreSQL is
    # independently exercised in test_postgres_storage.py.
    store=SimpleNamespace(database=SimpleNamespace(postgres=True),transaction=local.transaction)
    artifacts=Artifacts(tmp_path/run,('private-value',),store)
    entry=artifacts.write('patch-1',{'summary':'private-value'})
    (tmp_path/run/'patch-1.json').unlink()
    assert read_durable(store,run,entry)=={'summary':'[redacted]'}
    with local.transaction() as db:
        db.execute('UPDATE artifact_records SET content=?',('{}',))
    with pytest.raises(Exception,match='integrity'):
        read_durable(store,run,entry)


def test_cloud_retention_without_runner_files_preserves_publishable_runs(tmp_path):
    from backend.retention import cleanup
    local=Store(tmp_path/'db',clock=lambda:20*86400);local.initialize()
    ids=[local.submit(URL),local.submit(URL)]
    with local.transaction() as db:
        for run,state in zip(ids,['failed','ready_to_publish']):
            db.execute('UPDATE runs SET status=?,updated_at=0 WHERE run_id=?',(state,run))
            db.execute("UPDATE jobs SET state='done' WHERE run_id=?",(run,))
            db.execute('INSERT INTO artifact_records VALUES(?,?,?,?)',(run,'plan.json','hash','{}'))
    store=SimpleNamespace(database=SimpleNamespace(postgres=True),transaction=local.transaction,
                          clock=local.clock,_event=local._event)
    assert cleanup(store,tmp_path)['runs']==[{'run_id':ids[0],'durable_artifacts':1}]
    cleanup(store,tmp_path,apply=True)
    with local.transaction() as db:
        assert db.execute('SELECT run_id FROM artifact_records').fetchone()[0]==ids[1]


def test_cloud_preflight_rejects_sqlite_dispatch_and_redacts_probe_errors(tmp_path,monkeypatch):
    from backend.cloud_preflight import check
    store=Store(tmp_path/'db');store.initialize()
    monkeypatch.setenv('TORQUE_WORKER_DISPATCH','github-actions')
    assert not check(store)['configured']
    monkeypatch.setenv('TORQUE_WORKER_DISPATCH','local')
    assert check(store,True)['live_verified']
    with store.transaction() as db:db.execute('DROP TABLE artifact_records')
    report=check(store,True)
    assert not report['configured'] and 'private' not in json.dumps(report)
