"""Bounded cloud storage/dispatch checks; never return DSNs or token values."""
import os
import httpx


def check(store, probe=False):
    mode=os.getenv('TORQUE_WORKER_DISPATCH','local')
    report={'database':'postgresql' if store.database.postgres else 'sqlite',
            'artifact_store':'private-database' if store.database.postgres else 'local-files',
            'dispatch':mode,'missing':[], 'live_verified':False}
    if mode not in {'local','github-actions'}:report['missing'].append('Unsupported TORQUE_WORKER_DISPATCH')
    if mode=='github-actions' and not store.database.postgres:
        report['missing'].append('Actions agent workers require PostgreSQL')
    if mode=='github-actions' and not os.getenv('TORQUE_ACTIONS_TOKEN'):
        report['missing'].append('TORQUE_ACTIONS_TOKEN missing')
    if probe and not report['missing']:
        try:
            with store.transaction() as db:
                version=db.execute('SELECT MAX(version) FROM schema_migrations').fetchone()[0]
                db.execute('SELECT COUNT(*) FROM artifact_records').fetchone()
                db.execute('SELECT COUNT(*) FROM dispatches').fetchone()
            if version != 2:raise ValueError('Schema version')
            if mode=='github-actions':
                from backend.dispatch import Dispatcher
                dispatcher=Dispatcher(store)
                try:
                    response=dispatcher.client.get(f'/repos/{dispatcher.repository}/actions/workflows/{dispatcher.workflow}')
                    response.raise_for_status()
                    if response.json().get('state')!='active':raise ValueError('Workflow inactive')
                finally:dispatcher.close()
            report['live_verified']=True
        except Exception:
            report['missing'].append('Cloud probe failed; verify database schema and workflow access')
    report['configured']=not report['missing']
    return report
