"""Scan bounded live Neatlogs readbacks without exporting payloads or secrets."""
import json
import os
from datetime import datetime, timezone
from urllib.parse import urlencode
from cryptography.fernet import Fernet
from backend.config import ROOT, Settings
from backend.store import Store
from backend.runtime import SECRET_NAMES
from backend.integrations.neatlogs_read import TraceReader, ReadbackUnavailable

TRACES = ('228da4f22bcbe4aeabf7bc797c9d89d1',
          '6be9d833a671bf62d4cc8504cfb64223',
          '23a018f3233355b837448eb9812b232b')


def main():
    settings = Settings.load()
    values = {os.getenv(name, '') for name in SECRET_NAMES} - {''}
    with Store(settings.database).transaction() as db:
        cipher = Fernet(os.environ['TORQUE_SESSION_ENCRYPTION_KEY'].encode())
        for (encrypted,) in db.execute('SELECT token FROM github_connections WHERE token != ?', ('',)):
            values.add(cipher.decrypt(encrypted.encode()).decode())
    values = [value for value in values if len(value) >= 12]
    def clean(payload):
        content = json.dumps(payload)
        return not any(value in content for value in values)
    results = []
    reader = TraceReader(wait_seconds=5)
    try:
        for trace_id in TRACES:
            try:
                # Verify complete finalized trace identity before auditing pages.
                verified = reader.read(trace_id)
                safe = clean(reader.get('traces/' + trace_id, lambda: None))
                cursor = None; count = 0
                for _ in range(4):
                    params = {'limit':50}
                    if cursor: params['cursor'] = cursor
                    page = reader.get('traces/' + trace_id + '/spans?' + urlencode(params), lambda: None)
                    safe = safe and clean(page)
                    count += len(page['spans'])
                    cursor = page.get('page', {}).get('nextCursor')
                    if not cursor: break
                if cursor or count != len(verified['spans']):
                    raise ReadbackUnavailable('Trace changed or pagination incomplete during audit')
                results.append({'trace_id':trace_id, 'finalized':True,
                                'spans_checked':count, 'current_credentials_absent':safe})
            except ReadbackUnavailable as exc:
                results.append({'trace_id':trace_id, 'verified':False, 'reason':str(exc)})
    finally:
        reader.close()
    report = {'checked_at':datetime.now(timezone.utc).isoformat(),
              'mode':'bounded-live-neatlogs-current-credential-audit', 'results':results,
              'passed':all(r.get('current_credentials_absent') is True for r in results),
              'raw_payloads_exported':False,
              'limitations':['Only three selected finalized application traces',
                             'Exact matching of current configured and decryptable user credentials',
                             'External access logs and unknown/rotated credentials are not covered']}
    folder = ROOT/'evidence/security'; folder.mkdir(parents=True, exist_ok=True)
    (folder/'neatlogs-credential-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    try: result = main()
    except Exception: raise SystemExit('Live trace audit incomplete; no exception payload exported') from None
    raise SystemExit(result)
