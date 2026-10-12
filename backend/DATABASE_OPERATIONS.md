# Shared database setup and backup operations

Neon schema version 1 is initialized. Local API and worker configuration now uses
a restricted runtime role via `TORQUE_DATABASE_URL`. The original owner URL is
saved separately as `TORQUE_MIGRATION_DATABASE_URL` in ignored `.env`.

The runtime role has table SELECT/INSERT/UPDATE/DELETE and event-sequence access,
but cannot create schemas, databases or roles and is not a superuser or an RLS
bypass role. Both trusted backend processes currently share this role; user
isolation remains enforced by Torque authorization. No browser database
credential is issued. SQL-created roles avoid the broad membership granted by
Neon's console-created roles; see [Neon role documentation](https://github.com/neondatabase/website/blob/main/content/docs/manage/roles.md).

## Provisioning and schema upgrades

Install `requirements.txt`, then run migrations manually:

```powershell
.\.venv\Scripts\python.exe -m backend migrate
```

This command prefers the migration URL. Regular PostgreSQL startup only checks
the installed schema version; it does not run DDL under the restricted runtime
credential. OAuth initialization and HTTP counters also avoid runtime DDL.

`python -m backend.database_roles` provisions a generated runtime role and saves
its credential directly to local `.env`. Re-runs reuse the saved role. The helper
never prints passwords or URLs. New migration tables require reviewed grants to
the runtime role before deployment.

For Render and GitHub Actions, provision **only the runtime**
`TORQUE_DATABASE_URL` from local `.env`. Keep `TORQUE_MIGRATION_DATABASE_URL` and
the original `DATABASE_URL`/`DATABASE_URL_POOLED` owner aliases out of those hosts.
Do not copy the whole local `.env` into production configuration.

The existing local SQLite database is preserved. Its run history has not been
imported into Neon; reconnect/login will create fresh cloud sessions. Keep the
current session encryption key securely if importing encrypted credentials later.

## Encrypted backup and restore drill

```powershell
.\.venv\Scripts\python.exe -m backend.database_backup
```

This explicitly:

1. Takes an online SQLite snapshot, including committed WAL data, without changing
   the source journal mode. Encrypts it and verifies an in-memory integrity check.
2. Exports the 14 PostgreSQL tables in a serialized Torque transaction and encrypts
   the archive with the configured Fernet session encryption key.
3. Restores PostgreSQL into a generated `torque_restore_*` schema, compares every
   backed-up row, restores the event sequence, and removes the temporary schema.
4. Writes only a safe summary under `evidence/deployment/`.

Encrypted archives reside in ignored `var/database-backups/*.fernet`. Their
paths are listed in `evidence/deployment/database-backup-checks.json`. Plaintext
credential-containing backup files are not written. Exports are capped at 32 MiB
and 100,000 rows per table; larger deployments need a reviewed streaming or
native PostgreSQL backup process.

The SQLite snapshot header is normalized for in-memory restore according to
[SQLite's documented WAL deserialize handling](https://sqlite.org/c3ref/deserialize.html);
the source database is untouched.

The current Neon backup contains the schema record because no cloud runs exist
yet. A separate populated fixture restore checks nonempty users, run history,
events, jobs and dispatch records in disposable schemas. It does not import demo
history into the live schema.

Before public release, copy encrypted archives to private off-machine storage and
keep the encryption key separately in a password manager. Local ignored backups
alone cannot protect against loss of this laptop. Backup scheduling and off-site
provisioning remain deployment tasks; this command is a manual drill.

## Production restore procedure

Stop new submissions and worker dispatch before a production restore. Create a
fresh database/branch, apply the matching migration version, restore a verified
archive with the owner credential, and reapply runtime grants. The current
`restore_check` helper deliberately restores only into a disposable schema; it
does not overwrite production tables.

Reconcile running job/publication leases and GitHub side effects before enabling
workers. Do not replay an archived running job or ambiguous publication merely
because its old lease expired. Verify row/content hashes, restore the event
sequence, test login/ownership, and switch API and worker together to the restored
runtime URL. Preserve the prior database until acceptance succeeds.

Neon free restore history is limited; check the project dashboard and current
plan documentation rather than treating it as a long-term backup. Match the
Render region to the Neon project's region when creating the API.
