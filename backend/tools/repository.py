"""Bounded immutable public-source snapshots; no repository code runs here."""
import io
from pathlib import Path
import re
import stat
import time
import logging
import zipfile
import httpx
from backend.models import PipelineError
from backend.tools.files import safe_path

log = logging.getLogger(__name__)

def extract_archive(data, root, max_bytes=128_000_000):
    root = Path(root)
    if root.exists():
        raise PipelineError("Run workspace already exists; interrupted work is not replayed")
    if len(data) > max_bytes:
        raise PipelineError("Repository archive exceeds download limit")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        entries = archive.infolist()
        if not entries or len(entries) > 20000:
            raise PipelineError("Repository archive has too many entries")
        prefix = entries[0].filename.split("/")[0] + "/"
        validated, total = [], 0
        names = set()
        for item in entries:
            if not item.filename.startswith(prefix):
                raise PipelineError("Archive contains multiple roots")
            name = item.filename[len(prefix):]
            if not name:
                continue
            if any(part.lower().startswith(".env") for part in name.split("/")):
                continue
            mode = item.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise PipelineError("Archive symlinks are unsupported")
            path = safe_path(root,name.rstrip("/"))
            if item.is_dir():
                continue
            total += item.file_size
            normalized = name.casefold()
            if total > max_bytes or normalized in names:
                raise PipelineError("Archive is oversized or contains duplicate paths")
            names.add(normalized)
            validated.append((item,path))
        root.mkdir(parents=True)
        for item,path in validated:
            path.parent.mkdir(parents=True,exist_ok=True)
            # ZipFile validates CRC; declared size was checked before extraction.
            path.write_bytes(archive.read(item))
    return root

def snapshot(owner, repository, sha, root, checkpoint):
    if not re.fullmatch("[0-9a-f]{40}",sha):
        raise PipelineError("Source revision must be immutable")
    checkpoint()
    content = bytearray()
    last_check = time.monotonic()
    last_progress = last_check
    log.info("Downloading pinned source archive")
    with httpx.stream("GET",f"https://codeload.github.com/{owner}/{repository}/zip/{sha}",
                      timeout=30,follow_redirects=False) as response:
        response.raise_for_status()
        for chunk in response.iter_bytes(chunk_size=65536):
            now = time.monotonic()
            # Cloud checkpoints perform authorization and database round trips.
            # Keep cancellation responsive without throttling every few chunks;
            # lease renewal runs independently in the worker heartbeat thread.
            if now - last_check >= 10:
                checkpoint()
                last_check = now
            content.extend(chunk)
            if len(content) > 128_000_000:
                raise PipelineError("Repository archive exceeds download limit")
            if now - last_progress >= 10:
                log.info("Source download: %.1f MiB",len(content)/1048576)
                last_progress = now
    checkpoint()
    log.info("Source downloaded; validating archive")
    return extract_archive(content,root)
