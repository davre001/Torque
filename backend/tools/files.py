"""Strict allowlisted text access; repository content is untrusted."""
import hashlib
import re
from pathlib import Path, PurePosixPath
from backend.models import PipelineError


def bounded_source_context(context, query='', max_bytes=12000):
    """Issue-relevant original lines for models; full hashes stay unchanged."""
    if not context:
        return {}
    terms = set(re.findall(r'[a-zA-Z_][a-zA-Z_0-9]{3,}', query.lower()))
    terms -= {'this', 'that', 'with', 'from', 'when', 'should', 'issue', 'please', 'have', 'does', 'there'}
    allowance = max_bytes // len(context)
    result = {}
    for name, record in context.items():
        content = record['content']
        if len(content.encode('utf-8')) <= allowance:
            result[name] = dict(record)
            continue
        lines = content.splitlines(keepends=True)
        scored = sorted(range(len(lines)), key=lambda i: (-sum(t in lines[i].lower() for t in terms), i))
        chosen, used = {}, 0
        for center in scored:
            if center in chosen:
                continue
            for index in range(max(0, center-3), min(len(lines), center+4)):
                if index in chosen:
                    continue
                text = f'[Original line {index+1}]\n' + lines[index]
                size = len(text.encode('utf-8'))
                if used + size <= allowance:
                    chosen[index] = text
                    used += size
            if used >= allowance-80:
                break
        excerpt = ''.join(chosen[i] for i in sorted(chosen))
        result[name] = {**record, 'content':excerpt, 'is_excerpt':True}
    return result

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

def investigation_context(context,terms_by_file,max_bytes=16000):
    """Select labeled excerpts using operator-reviewed terms, never model instructions."""
    result = {}
    for name,record in context.items():
        terms = terms_by_file.get(name)
        if terms is None:
            result[name] = dict(record)
            continue
        if not terms or len(terms) > 10 or any(not term or len(term) > 80 for term in terms):
            raise PipelineError("Invalid investigation context terms")
        lines = record["content"].splitlines(keepends=True)
        selected = set()
        for index,line in enumerate(lines):
            if any(term in line for term in terms):
                selected.update(range(max(0,index-12),min(len(lines),index+13)))
        if not selected:
            raise PipelineError("Reviewed investigation terms did not match; review the recipe")
        excerpts,previous = [], -2
        for index in sorted(selected):
            if index != previous+1:
                excerpts.append(f"\n[Excerpt starts at original line {index+1}]\n")
            excerpts.append(lines[index])
            previous = index
        result[name] = {**record,"content":"".join(excerpts),"is_excerpt":True}
    if sum(len(record["content"].encode("utf-8")) for record in result.values()) > max_bytes:
        raise PipelineError("Investigation context exceeds size limit; review context selection")
    return result
