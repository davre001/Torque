"""Encrypted bounded backups; restore drills always use disposable schemas."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import uuid
from urllib.parse import urlsplit,urlunsplit,parse_qsl,urlencode
from cryptography.fernet import Fernet
from backend.config import ROOT,Settings
from backend.database_roles import TABLES

MAX_BYTES=32*1024*1024


def cipher():
    Settings.load()
    return Fernet(os.environ['TORQUE_SESSION_ENCRYPTION_KEY'].encode())


def snapshot(store):
    tables={}
    used=0
    with store.transaction() as db:
        for table in TABLES:
            tables[table]=[]
            offset=0
            while True:
                rows=db.execute('SELECT * FROM '+table+' LIMIT 8 OFFSET ?',(offset,)).fetchall()
                for row in rows:
                    item=dict(row)
                    used+=len(json.dumps(item,sort_keys=True,ensure_ascii=True,allow_nan=False).encode())
                    if used>MAX_BYTES:raise ValueError('Backup size bound exceeded')
                    tables[table].append(item)
                offset+=len(rows)
                if offset>100000:raise ValueError('Backup row bound exceeded')
                if len(rows)<8:break
    value={'format':'torque-postgres-v1','tables':tables}
    raw=json.dumps(value,sort_keys=True,ensure_ascii=True,allow_nan=False).encode()
    if len(raw)>MAX_BYTES:raise ValueError('Backup size bound exceeded')
    return raw


def save(raw,kind):
    if len(raw)>MAX_BYTES:raise ValueError('Backup size bound exceeded')
    root=ROOT/'var'/'database-backups';root.mkdir(parents=True,exist_ok=True)
    path=root/(kind+'-'+uuid.uuid4().hex+'.fernet')
    with path.open('xb') as stream:stream.write(cipher().encrypt(raw))
    return path


def backup_sqlite():
    path=Path(os.getenv('TORQUE_DATABASE',str(ROOT/'var'/'torque.sqlite3')))
    if not path.exists():return {'sqlite_present':False}
    # Online backup includes WAL state; serialize in memory so no plaintext copy
    # of credentials is left in a backup directory.
    with sqlite3.connect('file:'+path.resolve().as_posix()+'?mode=ro',uri=True) as source:
        if source.execute('PRAGMA page_count').fetchone()[0]*source.execute('PRAGMA page_size').fetchone()[0]>MAX_BYTES:
            raise ValueError('SQLite backup size bound exceeded')
        with sqlite3.connect(':memory:') as target:
            source.backup(target)
            raw=target.serialize()
            # SQLite's documented deserialize workaround for a fully materialized
            # WAL snapshot. Change only the backup header, never the source DB.
            raw=raw[:18]+bytes((1,1))+raw[20:]
    backup=save(raw,'sqlite')
    recovered=cipher().decrypt(backup.read_bytes())
    with sqlite3.connect(':memory:') as restored:
        restored.deserialize(recovered)
        integrity=restored.execute('PRAGMA integrity_check').fetchone()[0]
    if integrity!='ok' or hashlib.sha256(recovered).digest()!=hashlib.sha256(raw).digest():
        raise ValueError('SQLite backup verification failed')
    return {'sqlite_present':True,'encrypted_backup':backup.relative_to(ROOT).as_posix(),
            'integrity_check':'ok','byte_match':True}


def restore_check(path,migration_url):
    import psycopg
    from psycopg import sql
    from backend.store import Store
    path=Path(path)
    if path.stat().st_size>MAX_BYTES*2:raise ValueError('Encrypted backup exceeds bound')
    raw=cipher().decrypt(path.read_bytes())
    if len(raw)>MAX_BYTES:raise ValueError('Backup exceeds bound')
    archive=json.loads(raw)
    if archive.get('format')!='torque-postgres-v1' or set(archive['tables'])!=set(TABLES):
        raise ValueError('Unsupported backup format')
    schema='torque_restore_'+uuid.uuid4().hex
    with psycopg.connect(migration_url,autocommit=True,connect_timeout=10,prepare_threshold=None) as admin:
        admin.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
    try:
        url=urlsplit(migration_url);options=dict(parse_qsl(url.query));options['options']='-csearch_path='+schema
        target=Store(urlunsplit(url._replace(query=urlencode(options))))
        target.initialize(migrate=True)
        with target.transaction() as db:
            db.execute('DELETE FROM schema_migrations')
            for table in TABLES:
                columns=[r[0] for r in db.execute('SELECT column_name FROM information_schema.columns WHERE table_schema=current_schema() AND table_name=?',(table,))]
                for row in archive['tables'][table]:
                    if set(row)!=set(columns):raise ValueError('Backup columns differ from schema')
                    db.execute('INSERT INTO '+table+' ('+','.join(columns)+') VALUES('+','.join('?' for _ in columns)+')',tuple(row[column] for column in columns))
            db.execute("SELECT setval(pg_get_serial_sequence('events','id'),COALESCE((SELECT MAX(id) FROM events),1),EXISTS(SELECT 1 FROM events))")
        restored=json.loads(snapshot(target))
        for table in TABLES:
            original=sorted(json.dumps(row,sort_keys=True) for row in archive['tables'][table])
            actual=sorted(json.dumps(row,sort_keys=True) for row in restored['tables'][table])
            if original!=actual:raise ValueError('Restore data differs from backup')
        return {'isolated_restore_passed':True,'tables_verified':len(TABLES),
                'rows_verified':sum(len(rows) for rows in restored['tables'].values()),
                'production_tables_modified':False}
    finally:
        with psycopg.connect(migration_url,autocommit=True,connect_timeout=10,prepare_threshold=None) as admin:
            admin.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))


def run():
    from backend.store import Store
    settings=Settings.load()
    local=backup_sqlite()
    backup=save(snapshot(Store(settings.database)),'postgres')
    migration=os.getenv('TORQUE_MIGRATION_DATABASE_URL') or str(settings.database)
    report={'sqlite':local,'postgres':{'encrypted_backup':backup.relative_to(ROOT).as_posix(),
                                      **restore_check(backup,migration)},'credentials_exported':False}
    path=ROOT/'evidence'/'deployment'/'database-backup-checks.json'
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    try:print(json.dumps(run(),indent=2))
    except Exception as exc:
        print(json.dumps({'verified':False,'error_type':type(exc).__name__}))
        raise SystemExit(1)
