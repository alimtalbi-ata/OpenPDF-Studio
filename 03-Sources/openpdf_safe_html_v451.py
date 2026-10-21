"""V45.1: bounded, exclusive publication of offline diagnostic HTML.

Author: Abdelhalim Talbi.

The exporter never overwrites an existing path, including a dangling symlink.
A same-directory hard link makes a completely written file visible atomically;
filesystems without hard-link support fail closed rather than silently exposing
partially written HTML. Source mutation is detected before publication, but a
concurrent writer is not prevented from modifying the source afterwards.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
import tempfile
from pathlib import Path
from typing import Callable

MAX_INPUT_BYTES = 25 * 1024 * 1024
MAX_HTML_BYTES = 64 * 1024 * 1024


def _read_source(source: Path, limit: int) -> tuple[bytes, os.stat_result]:
    if source.is_symlink():
        raise ValueError('Diagnostic input must not be a symbolic link')
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0)
    if hasattr(os, 'O_NOFOLLOW'):
        flags |= os.O_NOFOLLOW
    fd = os.open(source, flags)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError('Diagnostic input must be a regular file')
        if before.st_size > limit:
            raise ValueError('Diagnostic input exceeds size limit')
        chunks = []
        total = 0
        while True:
            chunk = os.read(fd, min(1024 * 1024, limit + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > limit:
                raise ValueError('Diagnostic input exceeds size limit')
        after = os.fstat(fd)
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
                after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
            raise ValueError('Diagnostic input changed during read')
        return b''.join(chunks), after
    finally:
        os.close(fd)


def _assert_source_unchanged(source: Path, original: bytes, identity: os.stat_result,
                             limit: int) -> None:
    current, metadata = _read_source(source, limit)
    if (metadata.st_dev, metadata.st_ino) != (identity.st_dev, identity.st_ino):
        raise ValueError('Diagnostic input was replaced during rendering')
    if hashlib.sha256(current).digest() != hashlib.sha256(original).digest():
        raise ValueError('Diagnostic input changed during rendering')


def export_html_report(source: Path, destination: Path,
                       renderer: Callable[[dict], str], *,
                       max_input_bytes: int = MAX_INPUT_BYTES,
                       max_html_bytes: int = MAX_HTML_BYTES) -> dict:
    """Render a JSON report and publish only if source/output contracts hold.

    Returns a size/hash receipt. `renderer` must produce a complete HTML string.
    The temporary file is fully flushed before publication. Existing outputs
    and symlinks are never overwritten; source and output must be distinct.
    """
    source, destination = Path(source), Path(destination)
    if destination.suffix.lower() not in ('.html', '.htm'):
        raise ValueError('Diagnostic destination must end with .html or .htm')
    if not destination.parent.is_dir():
        raise FileNotFoundError('Diagnostic destination directory does not exist')
    if os.path.lexists(destination):
        raise FileExistsError(f'Diagnostic destination already exists: {destination}')
    original, identity = _read_source(source, max_input_bytes)
    try:
        report = json.loads(original.decode('utf-8-sig'),
                            parse_constant=lambda value: (_ for _ in ()).throw(
                                ValueError(f'Invalid JSON constant: {value}')))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError('Diagnostic input is not valid UTF-8 JSON') from exc
    if not isinstance(report, dict):
        raise ValueError('Diagnostic report must be a JSON object')
    html = renderer(report)
    if not isinstance(html, str):
        raise TypeError('Diagnostic renderer must return HTML text')
    payload = html.encode('utf-8')
    if len(payload) > max_html_bytes:
        raise ValueError('Diagnostic HTML exceeds size limit')
    _assert_source_unchanged(source, original, identity, max_input_bytes)
    fd, temp_name = tempfile.mkstemp(prefix='.openpdf-html-', suffix='.tmp',
                                     dir=destination.parent)
    stage = Path(temp_name)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        _assert_source_unchanged(source, original, identity, max_input_bytes)
        # Same-directory link is exclusive and atomic on NTFS and POSIX FS.
        # Do not fall back to os.replace or a non-atomic streaming copy.
        os.link(stage, destination)
        if os.name != 'nt':
            try:
                directory = os.open(destination.parent, os.O_RDONLY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
            except OSError:
                # Directory sync is not universally supported. File was fsynced.
                pass
        return {'size_bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest(),
                'destination': str(destination)}
    finally:
        stage.unlink(missing_ok=True)
