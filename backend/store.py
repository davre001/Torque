"""Durable SQLite queue with short transactions and fenced worker writes."""
from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
import time
import uuid
from backend.models import Conflict, LeaseLost, Status, TERMINAL

class Store:
    def __init__(self, path: Path, clock=time.time):
        self.path, self.clock = Path(path), clock

    @contextmanager
    def transaction(self):
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def initialize(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY, github_login TEXT, created_at REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id),
                    issue_url TEXT NOT NULL, status TEXT NOT NULL, current_agent TEXT,
                    created_at REAL NOT NULL, updated_at REAL NOT NULL,
                    cancel_requested INTEGER NOT NULL DEFAULT 0,
                    idempotency_key TEXT, error TEXT, pr_url TEXT,
                    result TEXT NOT NULL DEFAULT '{}', UNIQUE(user_id,idempotency_key));
                CREATE TABLE IF NOT EXISTS jobs (
                    run_id TEXT PRIMARY KEY REFERENCES runs(run_id), state TEXT NOT NULL,
                    owner TEXT, lease_until REAL, heartbeat REAL, executions INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS attempts (
                    run_id TEXT NOT NULL REFERENCES runs(run_id), number INTEGER NOT NULL,
                    record TEXT NOT NULL, PRIMARY KEY(run_id,number));
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL REFERENCES runs(run_id),
                    created_at REAL NOT NULL, data TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS events_run ON events(run_id,id);
                CREATE INDEX IF NOT EXISTS jobs_state ON jobs(state,lease_until);
                CREATE TABLE IF NOT EXISTS publications (
                    run_id TEXT PRIMARY KEY REFERENCES runs(run_id), destination TEXT NOT NULL,
                    owner TEXT, lease_until REAL, commit_sha TEXT, pr_url TEXT);
                PRAGMA user_version=1;
            """)

    def _event(self, db, run_id, data):
        db.execute("INSERT INTO events(run_id,created_at,data) VALUES(?,?,?)", (run_id,self.clock(),json.dumps(data)))

    def submit(self, issue_url, user_id="operator", idempotency_key=None):
        with self.transaction() as db:
            if idempotency_key:
                old = db.execute("SELECT * FROM runs WHERE user_id=? AND idempotency_key=?", (user_id,idempotency_key)).fetchone()
                if old:
                    if old["issue_url"] != issue_url:
                        raise Conflict("Idempotency key already used for another issue")
                    return old["run_id"]
            db.execute("INSERT OR IGNORE INTO users(id,created_at) VALUES(?,?)", (user_id,self.clock()))
            run_id = uuid.uuid4().hex
            db.execute("INSERT INTO runs(run_id,user_id,issue_url,status,created_at,updated_at,idempotency_key) VALUES(?,?,?,?,?,?,?)", (run_id,user_id,issue_url,Status.QUEUED,self.clock(),self.clock(),idempotency_key))
            db.execute("INSERT INTO jobs(run_id,state) VALUES(?, 'queued')", (run_id,))
            self._event(db,run_id,{"status":"queued"})
            return run_id

    def get(self, run_id, user_id=None):
        with self.transaction() as db:
            row = db.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
            if row is None or (user_id is not None and row["user_id"] != user_id):
                return None
            result = dict(row)
            result["result"] = json.loads(result["result"])
            result["cancel_requested"] = bool(result["cancel_requested"])
            result["attempts"] = [json.loads(r[0]) for r in db.execute("SELECT record FROM attempts WHERE run_id=? ORDER BY number", (run_id,))]
            return result

    def history(self, user_id, limit=50):
        with self.transaction() as db:
            return [dict(r) for r in db.execute("SELECT run_id,issue_url,status,created_at,updated_at,pr_url FROM runs WHERE user_id=? ORDER BY created_at DESC LIMIT ?", (user_id,limit))]

    def events(self, run_id, after=0):
        with self.transaction() as db:
            return [{"id":r["id"],"created_at":r["created_at"],**json.loads(r["data"])} for r in db.execute("SELECT * FROM events WHERE run_id=? AND id>? ORDER BY id LIMIT 100", (run_id,after))]

    def claim(self, lease_seconds):
        with self.transaction() as db:
            expired = db.execute("SELECT run_id FROM jobs WHERE state='running' AND lease_until<=?", (self.clock(),)).fetchall()
            for row in expired:
                db.execute("UPDATE runs SET status='interrupted',current_agent=NULL,updated_at=?,error=? WHERE run_id=?", (self.clock(),"Worker lease expired; inspect artifacts before starting a new run",row[0]))
                db.execute("UPDATE jobs SET state='done',owner=NULL WHERE run_id=?", (row[0],))
                self._event(db,row[0],{"status":"interrupted"})
            # Prototype concurrency is one across worker processes, not one per process.
            if db.execute("SELECT 1 FROM jobs WHERE state='running' LIMIT 1").fetchone():
                return None
            row = db.execute("SELECT jobs.run_id FROM jobs JOIN runs USING(run_id) WHERE jobs.state='queued' ORDER BY runs.created_at LIMIT 1").fetchone()
            if not row:
                return None
            owner = uuid.uuid4().hex
            db.execute("UPDATE jobs SET state='running',owner=?,lease_until=?,heartbeat=?,executions=executions+1 WHERE run_id=?", (owner,self.clock()+lease_seconds,self.clock(),row[0]))
            return row[0], owner

    def _owns(self, db, run_id, owner):
        if not db.execute("SELECT 1 FROM jobs WHERE run_id=? AND owner=? AND state='running' AND lease_until>?", (run_id,owner,self.clock())).fetchone():
            raise LeaseLost("Worker no longer owns this job")

    def heartbeat(self, run_id, owner, lease_seconds):
        with self.transaction() as db:
            self._owns(db,run_id,owner)
            db.execute("UPDATE jobs SET lease_until=?,heartbeat=? WHERE run_id=?", (self.clock()+lease_seconds,self.clock(),run_id))

    def update(self, run_id, owner, status, *, error=None, result=None, attempt=None):
        status = Status(status)
        with self.transaction() as db:
            self._owns(db,run_id,owner)
            if status == Status.COMPLETED and not db.execute("SELECT 1 FROM runs WHERE run_id=? AND pr_url IS NOT NULL", (run_id,)).fetchone():
                raise Conflict("Completed runs require an actual recorded PR URL")
            db.execute("UPDATE runs SET status=?,current_agent=?,updated_at=?,error=?,result=COALESCE(?,result) WHERE run_id=?", (status,None if status in TERMINAL else status,self.clock(),error,json.dumps(result) if result is not None else None,run_id))
            if attempt is not None:
                db.execute("INSERT INTO attempts VALUES(?,?,?)", (run_id,attempt["number"],json.dumps(attempt)))
            self._event(db,run_id,{"status":status,"error":error})
            if status in TERMINAL:
                db.execute("UPDATE jobs SET state='done',owner=NULL,lease_until=NULL WHERE run_id=?", (run_id,))

    def cancel(self, run_id, user_id):
        with self.transaction() as db:
            row = db.execute("SELECT status FROM runs WHERE run_id=? AND user_id=?", (run_id,user_id)).fetchone()
            if not row:
                raise KeyError(run_id)
            if row[0] in TERMINAL:
                raise Conflict("Run is already finished")
            if row[0] == Status.PUBLISHING:
                raise Conflict("Publication cannot be cancelled after GitHub writes start; inspect the PR or retry publication")
            status = Status.CANCELLED if row[0] == Status.QUEUED else row[0]
            db.execute("UPDATE runs SET cancel_requested=1,status=?,updated_at=? WHERE run_id=?", (status,self.clock(),run_id))
            if status == Status.CANCELLED:
                db.execute("UPDATE jobs SET state='done' WHERE run_id=? AND state='queued'", (run_id,))
            self._event(db,run_id,{"status":status,"cancel_requested":True})

    def claim_publication(self,run_id,user_id,destination):
        with self.transaction() as db:
            if user_id != "operator" and not db.execute("SELECT 1 FROM github_connections WHERE user_id=? AND revoked=0 AND expires>?",(user_id,self.clock())).fetchone():
                raise Conflict("GitHub disconnected or authorization expired")
            run=db.execute("SELECT * FROM runs WHERE run_id=? AND user_id=?",(run_id,user_id)).fetchone()
            if not run or run['status'] not in {Status.READY,Status.PUBLISHING}:
                raise Conflict("Only a verified ready-to-publish run can be published")
            if not json.loads(run['result']).get('verified') or run['cancel_requested']:
                raise Conflict("Run is not verified or was cancelled")
            publication=db.execute("SELECT * FROM publications WHERE run_id=?",(run_id,)).fetchone()
            if publication:
                if publication['destination'] != destination:
                    raise Conflict("Publication destination cannot change after the first request")
                if publication['owner'] and publication['lease_until'] > self.clock():
                    raise Conflict("Publication is already in progress")
            owner=uuid.uuid4().hex
            db.execute("INSERT INTO publications(run_id,destination,owner,lease_until) VALUES(?,?,?,?) "
                       "ON CONFLICT(run_id) DO UPDATE SET owner=excluded.owner,lease_until=excluded.lease_until",
                       (run_id,destination,owner,self.clock()+900))
            db.execute("UPDATE runs SET status='publishing',current_agent='publishing',error=NULL,updated_at=? WHERE run_id=?",
                       (self.clock(),run_id))
            self._event(db,run_id,{'status':'publishing','destination':destination})
            return owner

    def finish_publication(self,run_id,owner,*,pr_url=None,commit_sha=None,error=None):
        with self.transaction() as db:
            row=db.execute("SELECT * FROM publications WHERE run_id=? AND owner=? AND lease_until>?",
                           (run_id,owner,self.clock())).fetchone()
            if not row:
                raise Conflict("Publication lease expired; reconcile with a new publish request")
            status=Status.COMPLETED if pr_url else Status.READY
            run=db.execute("SELECT result FROM runs WHERE run_id=?",(run_id,)).fetchone()
            result=json.loads(run[0])
            if pr_url:
                result.update(publication_available=True,published_commit_sha=commit_sha,
                              destination_repository=row['destination'])
            db.execute("UPDATE runs SET status=?,current_agent=NULL,pr_url=?,error=?,result=?,updated_at=? WHERE run_id=?",
                       (status,pr_url,error,json.dumps(result),self.clock(),run_id))
            db.execute("UPDATE publications SET owner=NULL,lease_until=NULL,commit_sha=?,pr_url=? WHERE run_id=?",
                       (commit_sha,pr_url,run_id))
            self._event(db,run_id,{'status':status,'pr_url':pr_url,'error':error})
