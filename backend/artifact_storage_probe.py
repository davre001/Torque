"""Read-only deployment metadata after isolated artifact integration checks."""
import json
from datetime import datetime, timezone
from pathlib import Path
from backend.config import ROOT, Settings
from backend.store import Store


def check():
    store = Store(Settings.load().database)
    if not store.database.postgres:
        raise ValueError('Artifact deployment verification requires PostgreSQL')
    store.initialize()
    with store.transaction() as db:
        table = db.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=current_schema() AND table_name='artifact_records'").fetchone()[0]
        permissions = {p: db.execute("SELECT has_table_privilege(current_user,'artifact_records',?)", (p,)).fetchone()[0]
                       for p in ['SELECT', 'INSERT', 'UPDATE', 'DELETE']}
        ddl = db.execute("SELECT has_schema_privilege(current_user,current_schema(),'CREATE')").fetchone()[0]
        public = db.execute("SELECT COUNT(*) FROM information_schema.table_privileges WHERE table_schema=current_schema() AND table_name='artifact_records' AND grantee='PUBLIC'").fetchone()[0]
    files = list((ROOT/'evidence/runs').rglob('*.json')) + list((ROOT/'evidence/recovery').rglob('*.json'))
    sizes = [p.stat().st_size for p in files]
    return {'checked_at': datetime.now(timezone.utc).isoformat(),
            'database_table_exists': bool(table), 'runtime_artifact_permissions': permissions,
            'runtime_schema_create_allowed': ddl, 'public_table_grants': public,
            'representative_json_records': len(sizes),
            'largest_representative_record_bytes': max(sizes, default=0),
            'all_representative_records_within_2_mib': all(s <= 2097152 for s in sizes),
            'production_data_modified': False,
            'limitations': ['Neon account storage allowance requires dashboard confirmation',
                            'Render and Actions runtime secret provisioning pending',
                            'Deployed logs and complete hosted flow not yet verified']}


if __name__ == '__main__':
    try:
        report = check()
        (ROOT/'evidence/deployment/private-artifact-checks.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps(report))
    except Exception as exc:
        raise SystemExit('Artifact metadata verification incomplete: '+type(exc).__name__) from None
