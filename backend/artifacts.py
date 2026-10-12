"""Atomic local evidence records; callers must sanitize content first."""
import hashlib
import json
import os
from pathlib import Path
import uuid
from backend.models import PipelineError

class Artifacts:
    def __init__(self, root, secrets=(), store=None):
        self.root = Path(root)
        self.secrets = tuple(value for value in secrets if value)
        self.store = store if store is not None and store.database.postgres else None

    def sanitize(self, value):
        if isinstance(value,str):
            for secret in self.secrets:
                value = value.replace(secret,"[redacted]")
            return value
        if isinstance(value,dict):
            return {key:self.sanitize(item) for key,item in value.items()}
        if isinstance(value,(list,tuple)):
            return [self.sanitize(item) for item in value]
        return value

    def write(self, name, value):
        if not name or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in name):
            raise PipelineError("Invalid artifact name")
        self.root.mkdir(parents=True,exist_ok=True)
        data = json.dumps(self.sanitize(value),ensure_ascii=self.store is not None,indent=2).encode()
        if len(data) > 2 * 1024 * 1024:
            raise PipelineError('Artifact exceeds the 2 MiB storage limit')
        sha = hashlib.sha256(data).hexdigest()
        if self.store is not None:
            with self.store.transaction() as db:
                old = db.execute('SELECT sha256 FROM artifact_records WHERE run_id=? AND name=?',
                                 (self.root.name,name+'.json')).fetchone()
                if old and old[0] != sha:
                    raise PipelineError('Durable artifact is immutable')
                total = db.execute('SELECT COALESCE(SUM(length(content)),0) FROM artifact_records WHERE run_id=?',
                                   (self.root.name,)).fetchone()[0]
                if not old and total + len(data) > 8*1024*1024:
                    raise PipelineError('Run artifacts exceed the 8 MiB storage allowance')
                db.execute('INSERT OR IGNORE INTO artifact_records VALUES(?,?,?,?)',
                           (self.root.name,name+'.json',sha,data.decode()))
        target = self.root/(name+".json")
        temporary = self.root/(name+"-"+uuid.uuid4().hex+".tmp")
        try:
            with temporary.open("xb") as stream:
                stream.write(data)
            os.replace(temporary,target)
        finally:
            temporary.unlink(missing_ok=True)
        return {"name":target.name,"sha256":sha}


def read_durable(store, run_id, entry):
    import re
    if not re.fullmatch('[a-f0-9]{32}',run_id) or not re.fullmatch(r'[a-z0-9-]+\.json',entry['name']):
        raise PipelineError('Invalid durable artifact identity')
    with store.transaction() as db:
        row = db.execute('SELECT sha256,content FROM artifact_records WHERE run_id=? AND name=? AND length(content)<=2097152',
                         (run_id,entry['name'])).fetchone()
    if row is None: raise PipelineError('Durable verification artifact unavailable')
    data = row['content'].encode()
    if len(data) > 2*1024*1024 or row['sha256'] != entry['sha256'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
        raise PipelineError('Durable artifact failed integrity verification')
    return json.loads(data)
