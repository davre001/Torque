"""Explicit local retention; durable history and reviewable publication stay intact."""
import json
import math
import re
import shutil
import stat
import uuid
from pathlib import Path
from backend.models import PipelineError

EXPIRED_STATES = {'completed', 'failed', 'cancelled', 'interrupted'}


def checked_directory(path, boundary):
    path, boundary = Path(path), Path(boundary).resolve()
    if not path.exists():
        return False
    if path.resolve() == boundary or not path.resolve().is_relative_to(boundary):
        raise PipelineError('Retention path escapes its runtime boundary')
    # Windows junctions and cloud/reparse links must never become deletion targets.
    for item in [path, *path.parents]:
        if item == boundary:
            break
        info = item.lstat()
        if item.is_symlink() or getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise PipelineError('Retention refuses linked runtime paths')
    if not path.is_dir():
        raise PipelineError('Retention expects a run directory')
    for item in path.rglob('*'):
        info = item.lstat()
        if item.is_symlink() or getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise PipelineError('Retention refuses links inside run directories')
    return True


def eligible(db, run_id, cutoff):
    row = db.execute('''SELECT runs.* FROM runs JOIN jobs USING(run_id)
        WHERE runs.run_id=? AND jobs.state='done'
        AND runs.updated_at<? AND NOT EXISTS
        (SELECT 1 FROM publications WHERE publications.run_id=runs.run_id
         AND publications.owner IS NOT NULL)''', (run_id, cutoff)).fetchone()
    return row if row and row['status'] in EXPIRED_STATES else None


def cleanup(store, root, days=7, apply=False):
    if not math.isfinite(days) or days < 1:
        raise PipelineError('Retention must keep at least one day of runtime files')
    root = Path(root).resolve()
    runtime = root / 'var'
    cutoff = store.clock() - days * 86400
    with store.transaction() as db:
        ids = [r[0] for r in db.execute('SELECT run_id FROM runs WHERE updated_at<?', (cutoff,))]
    report = {'dry_run': not apply, 'keep_days': days, 'runs': [], 'blocked': []}
    for run_id in ids:
        if not re.fullmatch('[a-f0-9]{32}', run_id):
            continue
        with store.transaction() as db:
            if eligible(db, run_id, cutoff) is None:
                continue
        try:
            targets = [runtime / kind / run_id for kind in ('workspaces', 'artifacts')]
            targets = [p for p in targets if checked_directory(p, root)]
            if not targets:
                continue
            if not apply:
                report['runs'].append({'run_id': run_id, 'directories': len(targets)})
                continue
            trash = runtime / 'retention-trash'
            trash.mkdir(exist_ok=True)
            checked_directory(trash, root)
            moved = []
            # Only renames and metadata occur while the SQLite lock is held.
            # Expensive recursive deletion happens after releasing it.
            with store.transaction() as db:
                row = eligible(db, run_id, cutoff)
                if row is None:
                    continue
                try:
                    for target in targets:
                        destination = trash / (run_id + '-' + target.parent.name + '-' + uuid.uuid4().hex)
                        target.rename(destination)
                        moved.append((target, destination))
                    result = json.loads(row['result'])
                    result['retention'] = {'local_files_expired': True, 'expired_at': store.clock()}
                    db.execute('UPDATE runs SET result=? WHERE run_id=?', (json.dumps(result), run_id))
                    store._event(db, run_id, {'local_files_expired': True})
                except BaseException:
                    for original, destination in reversed(moved):
                        destination.rename(original)
                    raise
            for _, destination in moved:
                if checked_directory(destination, root):
                    shutil.rmtree(destination)
            report['runs'].append({'run_id': run_id, 'directories': len(moved)})
        except (OSError, PipelineError):
            report['blocked'].append({'run_id': run_id, 'reason': 'Unsafe path or local filesystem operation failed; inspect runtime files'})
    return report
