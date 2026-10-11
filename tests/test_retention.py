import json
import pytest
from backend.store import Store
from backend.retention import cleanup
from backend.models import PipelineError


def setup(tmp_path):
    store = Store(tmp_path/'var'/'history.db', clock=lambda: 20*86400)
    store.initialize()
    return store


def run(store, root, status='failed', updated=0, job='done'):
    rid = store.submit('https://github.com/owner/repo/issues/1')
    with store.transaction() as db:
        db.execute('UPDATE runs SET status=?,updated_at=?,pr_url=? WHERE run_id=?',
                   (status, updated, 'https://github.com/owner/repo/pull/1' if status=='completed' else None, rid))
        db.execute('UPDATE jobs SET state=? WHERE run_id=?', (job,rid))
    for kind in ('workspaces','artifacts'):
        p=root/'var'/kind/rid;p.mkdir(parents=True);(p/'keep.txt').write_text('fixture')
    return rid


def test_preview_and_apply_preserve_database_history_and_committed_evidence(tmp_path):
    store=setup(tmp_path);rid=run(store,tmp_path,'completed')
    evidence=tmp_path/'evidence'/rid;evidence.mkdir(parents=True);(evidence/'run.json').write_text('{}')
    assert cleanup(store,tmp_path)['runs']==[{'run_id':rid,'directories':2}]
    assert (tmp_path/'var/workspaces'/rid).exists()
    report=cleanup(store,tmp_path,apply=True)
    assert not report['blocked']
    assert not (tmp_path/'var/workspaces'/rid).exists()
    saved=store.get(rid)
    assert saved['status']=='completed' and saved['pr_url'].endswith('/pull/1')
    assert saved['result']['retention']['local_files_expired']
    assert (evidence/'run.json').exists()
    assert cleanup(store,tmp_path,apply=True)['runs']==[]


@pytest.mark.parametrize('status,updated,job',[
    ('queued',0,'queued'),('investigating',0,'running'),
    ('ready_to_publish',0,'done'),('publishing',0,'done'),
    ('failed',19*86400,'done'),('failed',0,'running')])
def test_active_publishable_and_recent_runs_are_protected(tmp_path,status,updated,job):
    store=setup(tmp_path);rid=run(store,tmp_path,status,updated,job)
    assert cleanup(store,tmp_path,apply=True)['runs']==[]
    assert (tmp_path/'var/workspaces'/rid).exists()


def test_pending_publication_and_orphan_directory_are_protected(tmp_path):
    store=setup(tmp_path);rid=run(store,tmp_path)
    with store.transaction() as db:
        db.execute('INSERT INTO publications(run_id,destination,owner) VALUES(?,?,?)',(rid,'owner/repo','pending-owner'))
    orphan=tmp_path/'var/artifacts'/('f'*32);orphan.mkdir()
    assert cleanup(store,tmp_path,apply=True)['runs']==[]
    assert orphan.exists() and (tmp_path/'var/workspaces'/rid).exists()


def test_links_cannot_delete_outside_runtime(tmp_path):
    store=setup(tmp_path);rid=run(store,tmp_path)
    outside=tmp_path/'outside';outside.mkdir();(outside/'valuable.txt').write_text('keep')
    try:
        (tmp_path/'var/workspaces'/rid/'link').symlink_to(outside,target_is_directory=True)
    except OSError:
        pytest.skip('Creating symlinks requires Windows Developer Mode or privileges')
    report=cleanup(store,tmp_path,apply=True)
    assert len(report['blocked'])==1
    assert (outside/'valuable.txt').read_text()=='keep'
    assert (tmp_path/'var/artifacts'/rid).exists()


def test_invalid_retention_cannot_remove_recent_files(tmp_path):
    store=setup(tmp_path)
    with pytest.raises(PipelineError):cleanup(store,tmp_path,days=0,apply=True)
