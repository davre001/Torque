import json
import subprocess
from backend.config import Settings
from backend.store import Store
from backend import security_audit


def test_audit_finds_removed_historical_secret_without_exporting_value(tmp_path, monkeypatch):
    def git(*args):
        subprocess.run(['git', *args], cwd=tmp_path, check=True, capture_output=True)
    git('init')
    secret = 'audit-fixture-credential-123456789'
    (tmp_path / 'removed.txt').write_text(secret)
    git('add', 'removed.txt')
    git('-c', 'user.name=Audit fixture', '-c', 'user.email=audit@example.test',
        'commit', '-m', 'Fixture historical credential')
    git('rm', 'removed.txt')
    git('-c', 'user.name=Audit fixture', '-c', 'user.email=audit@example.test',
        'commit', '-m', 'Remove fixture credential')
    store = Store(tmp_path / 'var/db'); store.initialize()
    monkeypatch.setattr(security_audit, 'ROOT', tmp_path)
    monkeypatch.setattr(Settings, 'load', lambda: Settings(store.path))
    monkeypatch.setenv('GITHUB_TOKEN', secret)
    report = security_audit.audit()
    assert not report['passed']
    assert any(f['scope'] == 'git-blob' for f in report['findings'])
    assert secret not in json.dumps(report)
