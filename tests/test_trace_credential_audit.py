import json
from cryptography.fernet import Fernet
from backend import trace_credential_audit as audit
from backend.config import Settings
from backend.store import Store


def test_raw_trace_secret_is_detected_without_exporting_payload(tmp_path, monkeypatch, capsys):
    store = Store(tmp_path/'db'); store.initialize()
    with store.transaction() as db:
        db.execute('CREATE TABLE github_connections (token TEXT)')
    monkeypatch.setattr(Settings, 'load', lambda: Settings(store.path))
    monkeypatch.setattr(audit, 'ROOT', tmp_path)
    monkeypatch.setenv('TORQUE_SESSION_ENCRYPTION_KEY', Fernet.generate_key().decode())
    secret = 'trace-audit-fixture-private-credential'
    monkeypatch.setenv('GITHUB_TOKEN', secret)
    class Reader:
        def __init__(self, **_): pass
        def read(self, _): return {'spans':[{'spanId':'root'}]}
        def get(self, path, _):
            if '/spans?' in path:
                return {'spans':[{'spanId':'root','attributes':{'payload':secret}}], 'page':{}}
            return {'traceId':path.split('/')[-1]}
        def close(self): pass
    monkeypatch.setattr(audit, 'TraceReader', Reader)
    assert audit.main() == 1
    output = (tmp_path/'evidence/security/neatlogs-credential-audit.json').read_text()
    assert secret not in output and secret not in capsys.readouterr().out
    report = json.loads(output)
    assert all(r['current_credentials_absent'] is False for r in report['results'])
    assert report['raw_payloads_exported'] is False
