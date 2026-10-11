"""Validate all edits before applying any; rollback a partial filesystem write."""
import hashlib
import os
from backend.models import PipelineError
from backend.tools.files import safe_path

def apply_patch(root, patch, editable_files, max_bytes=100000):
    changes, seen, total = [], set(), 0
    for edit in patch.edits:
        if edit.path not in editable_files or edit.path in seen:
            raise PipelineError("Patch touches an unapproved or duplicate file")
        seen.add(edit.path)
        target = safe_path(root,edit.path)
        if not target.is_file() or target.stat().st_size > max_bytes:
            raise PipelineError("Patch target missing or oversized")
        previous = target.read_bytes()
        if hashlib.sha256(previous).hexdigest() != edit.original_sha256:
            raise PipelineError("Patch source hash is stale")
        if edit.replacements is not None:
            try:
                text = previous.decode("utf-8")
            except UnicodeDecodeError:
                raise PipelineError("Patch target is not UTF-8") from None
            for replacement in edit.replacements:
                if text.count(replacement.search) != 1:
                    raise PipelineError("Patch search must match exactly once")
                text = text.replace(replacement.search,replacement.replacement,1)
                if len(text.encode("utf-8")) > max_bytes:
                    raise PipelineError("Patch exceeds size limit")
            content = text.encode("utf-8")
        else:
            content = edit.content.encode("utf-8")
        total += len(previous) + len(content)
        if total > max_bytes or b"\x00" in content:
            raise PipelineError("Patch exceeds size limit or contains binary content")
        changes.append((target,previous,content))
    if all(old == new for _,old,new in changes):
        raise PipelineError("Patch makes no changes")
    try:
        for target,_,content in changes:
            temporary = target.with_name(target.name+".torque-tmp")
            if temporary.exists():
                raise PipelineError("Temporary patch path already exists")
            try:
                with temporary.open("xb") as stream:
                    stream.write(content)
                os.replace(temporary,target)
            finally:
                temporary.unlink(missing_ok=True)
    except BaseException:
        for target,previous,_ in changes:
            target.write_bytes(previous)
        raise
    return hashlib.sha256(b"".join(target.relative_to(root).as_posix().encode()+b"\0"+content for target,_,content in changes)).hexdigest()
