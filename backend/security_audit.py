"""Read-only local credential audit. Reports locations, never credential values."""
import json
import os
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from backend.config import ROOT, Settings


def audit():
    settings = Settings.load()
    from backend.runtime import SECRET_NAMES
    values = {os.getenv(name, '') for name in SECRET_NAMES} - {''}
    connection_tokens = 0
    with sqlite3.connect(settings.database) as db:
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if 'github_connections' in tables:
            from cryptography.fernet import Fernet
            cipher = Fernet(os.environ['TORQUE_SESSION_ENCRYPTION_KEY'].encode())
            for (encrypted,) in db.execute('SELECT token FROM github_connections WHERE token != ?', ('',)):
                values.add(cipher.decrypt(encrypted.encode()).decode())
                connection_tokens += 1
        records = list(db.execute('SELECT result FROM runs'))
        records += list(db.execute('SELECT record FROM attempts'))
        records += list(db.execute('SELECT data FROM events'))
    needles = [v.encode() for v in values if len(v) >= 12]
    def leaked(data):
        return any(value in data for value in needles)
    findings = []
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=ROOT, stderr=subprocess.DEVNULL)
    tracked = git('ls-files', '-z').decode().split('\0')
    files = {ROOT / name for name in tracked if name}
    files.update((ROOT / 'evidence').rglob('*'))
    files.update((ROOT / 'var/artifacts').rglob('*'))
    scanned = 0
    for path in sorted(files):
        if path.is_file():
            scanned += 1
            if leaked(path.read_bytes()):
                findings.append({'scope': 'file', 'location': path.relative_to(ROOT).as_posix()})
    for index, (record,) in enumerate(records):
        if leaked(record.encode()):
            findings.append({'scope': 'persisted-response-data', 'location': str(index)})
    refs = git('for-each-ref', '--format=%(objectname)').decode().splitlines()
    objects = git('rev-list', '--objects', 'HEAD', *refs).splitlines()
    blobs = 0
    with subprocess.Popen(['git', 'cat-file', '--batch'], cwd=ROOT,
                          stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL) as process:
        for obj in objects:
            oid = obj.split(b' ', 1)[0]
            process.stdin.write(oid + b'\n'); process.stdin.flush()
            header = process.stdout.readline().split()
            if len(header) != 3:
                raise RuntimeError('Unable to inspect Git object')
            size = int(header[2]); remaining = size; tail = b''; found = False
            overlap = max([len(v) for v in needles] + [1]) - 1
            while remaining:
                chunk = process.stdout.read(min(65536, remaining))
                if not chunk:
                    raise RuntimeError('Incomplete Git object')
                remaining -= len(chunk)
                data = tail + chunk
                if header[1] == b'blob' and leaked(data): found = True
                tail = data[-overlap:] if overlap else b''
            process.stdout.read(1)
            if header[1] == b'blob':
                blobs += 1
                if found: findings.append({'scope': 'git-blob', 'location': oid.decode()})
        process.stdin.close()
        if process.wait(timeout=10): raise RuntimeError('Git object scan failed')
    return {'checked_at': datetime.now(timezone.utc).isoformat(),
            'mode': 'read-only-current-credential-exclusion-audit',
            'tracked_and_artifact_files': scanned, 'persisted_response_records': len(records),
            'reachable_git_blobs': blobs, 'connection_credentials_checked': connection_tokens,
            'findings': findings, 'passed': not findings,
            'limitations': ['Exact matching of currently configured secrets and decryptable user tokens only',
                            'Unknown or rotated credentials are not covered',
                            'Remote Git objects, live dashboard payloads, and deployment access logs are not inspected',
                            'Broken local refs are excluded; valid refs and HEAD are scanned',
                            'Session and CSRF values intentionally returned to their owner are not secret scan targets']}


if __name__ == '__main__':
    try:
        report = audit()
        folder = ROOT / 'evidence/security'; folder.mkdir(parents=True, exist_ok=True)
        (folder / 'credential-audit.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
        raise SystemExit(0 if report['passed'] else 1)
    except Exception:
        raise SystemExit('Credential audit incomplete; no exception payload exported') from None
