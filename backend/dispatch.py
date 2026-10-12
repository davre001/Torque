"""Durable Actions outbox. Ambiguous POSTs reuse an identity and job leases."""
import os
import re
import uuid
import httpx
from backend.models import PipelineError


class Dispatcher:
    def __init__(self, store, client=None):
        self.store = store
        self.repository = os.getenv('TORQUE_ACTIONS_REPOSITORY','davre001/Torque')
        self.ref = os.getenv('TORQUE_ACTIONS_REF','main')
        self.token = os.getenv('TORQUE_ACTIONS_TOKEN','')
        self.workflow = 'torque-agent-worker.yml'
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', self.repository):
            raise PipelineError('Invalid Actions repository')
        self.client = client or httpx.Client(base_url='https://api.github.com',timeout=20,
            headers={'Authorization':'Bearer '+self.token,'Accept':'application/vnd.github+json'},
            follow_redirects=False)

    def close(self):
        self.client.close()

    def dispatch(self, run_id):
        now, owner = self.store.clock(), uuid.uuid4().hex
        with self.store.transaction() as db:
            job = db.execute('SELECT * FROM jobs WHERE run_id=?',(run_id,)).fetchone()
            row = db.execute('SELECT * FROM dispatches WHERE run_id=?',(run_id,)).fetchone()
            if not job or job['state'] != 'queued': return False
            if not row:
                db.execute('INSERT INTO dispatches(run_id,request_id,state,updated_at) VALUES(?,?,?,?)',
                           (run_id,uuid.uuid4().hex,'pending',now))
                row = db.execute('SELECT * FROM dispatches WHERE run_id=?',(run_id,)).fetchone()
            if row['lease_until'] and row['lease_until'] > now: return False
            if row['updated_at'] > now-60 and row['state'] != 'pending': return False
            db.execute("UPDATE dispatches SET owner=?,lease_until=?,state='sending',attempts=attempts+1,updated_at=? WHERE run_id=?",
                       (owner,now+60,now,run_id))
            request_id = row['request_id']
        state = 'uncertain'
        try:
            if not self.token: raise PipelineError('Actions dispatch credential missing')
            # Reconcile before re-sending. A duplicate accepted dispatch is still
            # harmless: targeted DB claims allow one execution and never replay.
            response = self.client.get(f'/repos/{self.repository}/actions/workflows/{self.workflow}/runs',
                                       params={'event':'workflow_dispatch','per_page':100})
            response.raise_for_status()
            match = next((r for r in response.json()['workflow_runs']
                          if r.get('display_title') == f'Torque agent {run_id} {request_id}'
                          and r.get('status') != 'completed'), None)
            if match:
                state = 'sent'
            else:
                response = self.client.post(f'/repos/{self.repository}/actions/workflows/{self.workflow}/dispatches',
                    json={'ref':self.ref,'inputs':{'run_id':run_id,'request_id':request_id}})
                response.raise_for_status()
                state = 'sent'
        except (httpx.HTTPError,PipelineError,ValueError,KeyError):
            pass  # No URLs, response bodies, or secrets in persisted errors.
        finally:
            with self.store.transaction() as db:
                db.execute('UPDATE dispatches SET state=?,owner=NULL,lease_until=NULL,updated_at=? WHERE run_id=? AND owner=?',
                           (state,self.store.clock(),run_id,owner))
        return state == 'sent'

    def reconcile(self):
        # Expire stale worker leases using the same fenced claim logic. A
        # deliberately nonexistent assigned ID prevents claiming queued work.
        self.store.claim(60,'00000000000000000000000000000000')
        with self.store.transaction() as db:
            ids = [r[0] for r in db.execute("SELECT run_id FROM jobs WHERE state='queued' LIMIT 20")]
        return {'checked':len(ids),'sent':sum(self.dispatch(run_id) for run_id in ids)}
