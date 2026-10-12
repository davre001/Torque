"""Provision one DML-only runtime role; keep the owner URL local for migrations."""
import json
import os
import secrets
import uuid
from urllib.parse import urlsplit,urlunsplit,quote
from dotenv import set_key
from backend.config import ROOT,Settings

TABLES=('schema_migrations','users','runs','jobs','attempts','events','publications',
        'admission_reservations','dispatches','artifact_records','oauth_states',
        'github_connections','browser_sessions','http_admission')


def provision():
    import psycopg
    from psycopg import sql
    settings=Settings.load()
    migration=os.getenv('TORQUE_MIGRATION_DATABASE_URL') or str(settings.database)
    runtime=str(settings.database)
    role=urlsplit(runtime).username
    reuse=bool(os.getenv('TORQUE_MIGRATION_DATABASE_URL') and role and role.startswith('torque_runtime_'))
    if not reuse:
        role='torque_runtime_'+uuid.uuid4().hex[:12]
        password=secrets.token_urlsafe(48)
        url=urlsplit(migration)
        runtime=urlunsplit(url._replace(netloc=quote(role)+':'+quote(password)+'@'+url.netloc.rsplit('@',1)[-1]))
        with psycopg.connect(migration,connect_timeout=10,prepare_threshold=None) as db:
            schema=db.execute('SELECT current_schema()').fetchone()[0]
            database=db.execute('SELECT current_database()').fetchone()[0]
            db.execute(sql.SQL('CREATE ROLE {} LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD {}').format(sql.Identifier(role),sql.Literal(password)))
            db.execute(sql.SQL('GRANT CONNECT ON DATABASE {} TO {}').format(sql.Identifier(database),sql.Identifier(role)))
            db.execute(sql.SQL('GRANT USAGE ON SCHEMA {} TO {}').format(sql.Identifier(schema),sql.Identifier(role)))
            for table in TABLES:
                db.execute(sql.SQL('GRANT SELECT,INSERT,UPDATE,DELETE ON TABLE {}.{} TO {}').format(sql.Identifier(schema),sql.Identifier(table),sql.Identifier(role)))
            sequence=db.execute("SELECT pg_get_serial_sequence('events','id')").fetchone()[0]
            sequence_name=sequence.split('.')[-1].strip('"')
            db.execute(sql.SQL('GRANT USAGE,SELECT ON SEQUENCE {}.{} TO {}').format(sql.Identifier(schema),sql.Identifier(sequence_name),sql.Identifier(role)))
            if db.execute('SELECT has_schema_privilege(%s,%s,\'CREATE\')',(role,schema)).fetchone()[0]:
                raise ValueError('Public schema grants CREATE; review privileges before enabling runtime role')
        # Save before probing so a transient network error does not lose the
        # generated credential. Re-runs reuse it instead of making more roles.
        set_key(str(ROOT/'.env'),'TORQUE_MIGRATION_DATABASE_URL',migration)
        set_key(str(ROOT/'.env'),'TORQUE_DATABASE_URL',runtime)
    from backend.store import Store
    store=Store(runtime);store.initialize()
    with store.transaction() as db:
        flags=db.execute('SELECT rolcreatedb,rolcreaterole,rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user').fetchone()
        ddl=db.execute("SELECT has_schema_privilege(current_user,current_schema(),'CREATE')").fetchone()[0]
    if any(flags) or ddl:raise ValueError('Runtime database privileges are too broad')
    return {'runtime_role_restricted':True,'schema_create_allowed':False,
            'migration_credential_separate':True,'credential_values_exported':False}


if __name__=='__main__':
    try:print(json.dumps(provision()))
    except Exception as exc:
        print(json.dumps({'configured':False,'error_type':type(exc).__name__}))
        raise SystemExit(1)
