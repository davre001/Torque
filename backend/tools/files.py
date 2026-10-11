"""Strict allowlisted text access; repository content is untrusted."""
import hashlib
from pathlib import Path, PurePosixPath
from backend.models import PipelineError

def safe_path(root: Path, name: str):
    path = PurePosixPath(name)
    if (not name or "\\" in name or ":" in name or path.is_absolute()
            or any(p.lower() in {".","..",".git"} for p in name.split("/"))
            or any(p.lower().startswith(".env") for p in path.parts)):
        raise PipelineError("Unsafe repository path rejected")
    reserved = {"con","prn","aux","nul",*(f"com{i}" for i in range(1,10)),*(f"lpt{i}" for i in range(1,10))}
    if any(part.endswith(("."," ")) or part.split(".")[0].lower() in reserved
           or any(c in part for c in '<>"|?*') for part in path.parts):
        raise PipelineError("Nonportable repository path rejected")
    root = root.resolve()
    target = root.joinpath(*path.parts)
    for parent in [target,*target.parents]:
        if parent == root:
            break
        if parent.is_symlink():
            raise PipelineError("Symlink paths are not allowed")
    if not target.resolve().is_relative_to(root):
        raise PipelineError("Repository path escapes workspace")
    return target

def read_files(root, names, max_bytes=100000):
    total, result = 0, {}
    for name in names:
        path = safe_path(root,name)
        if not path.is_file() or path.stat().st_size > max_bytes:
            raise PipelineError("Context file missing or exceeds size limit")
        data = path.read_bytes()
        total += len(data)
        if total > max_bytes:
            raise PipelineError("Repository context exceeds size limit")
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise PipelineError("Only UTF-8 text files are supported") from exc
        result[name] = {"content":text,"sha256":hashlib.sha256(data).hexdigest()}
    return result
