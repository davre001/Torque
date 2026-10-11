"""Atomic local evidence records; callers must sanitize content first."""
import hashlib
import json
import os
from pathlib import Path
import uuid
from backend.models import PipelineError

class Artifacts:
    def __init__(self, root, secrets=()):
        self.root = Path(root)
        self.secrets = tuple(value for value in secrets if value)

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
        data = json.dumps(self.sanitize(value),ensure_ascii=False,indent=2).encode()
        target = self.root/(name+".json")
        temporary = self.root/(name+"-"+uuid.uuid4().hex+".tmp")
        try:
            with temporary.open("xb") as stream:
                stream.write(data)
            os.replace(temporary,target)
        finally:
            temporary.unlink(missing_ok=True)
        return {"name":target.name,"sha256":hashlib.sha256(data).hexdigest()}
