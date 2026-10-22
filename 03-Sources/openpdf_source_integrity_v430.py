"""Detect concurrent PDF source edits before publishing compressed output.
Author: Abdelhalim Talbi. Uses bounded-memory SHA-256 and file identity checks.
"""
from dataclasses import dataclass
import hashlib
import os

_CHUNK = 1024 * 1024

@dataclass(frozen=True)
class SourceFingerprint:
    device: int
    inode: int
    size: int
    modified_ns: int
    changed_ns: int
    sha256: str

def _identity(st):
    return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)

def fingerprint_source(source):
    """Hash a stable file handle and check pathname replacement."""
    with open(source, 'rb') as stream:
        before = os.fstat(stream.fileno())
        digest = hashlib.sha256()
        for block in iter(lambda: stream.read(_CHUNK), b''):
            digest.update(block)
        after = os.fstat(stream.fileno())
    current = os.stat(source)
    if _identity(before) != _identity(after) or _identity(after) != _identity(current):
        raise RuntimeError('Source modifiée pendant la compression : sortie rejetée')
    return SourceFingerprint(*_identity(after), digest.hexdigest())

def verify_source_unchanged(source, original):
    try:
        current = fingerprint_source(source)
    except (OSError, RuntimeError) as exc:
        raise RuntimeError('Source modifiée pendant la compression : sortie rejetée') from exc
    if current != original:
        raise RuntimeError('Source modifiée pendant la compression : sortie rejetée')
    return current.sha256
