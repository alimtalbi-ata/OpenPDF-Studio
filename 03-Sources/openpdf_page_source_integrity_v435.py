"""V43.5: verify PDF source identity and SHA-256 before publishing page operations.

Author: Abdelhalim Talbi. Uses bounded memory; does not lock sources.
"""
from dataclasses import dataclass
import hashlib
import os


@dataclass(frozen=True)
class SourceSnapshot:
    device: int
    inode: int
    size: int
    mtime_ns: int
    ctime_ns: int
    digest: str


# On Windows, st_ctime_ns represents creation time, not POSIX change time.
# NTFS can expose inconsistent creation timestamps via fstat/stat immediately
# after PDF creation; retain device/inode/size/mtime and SHA-256 checks.
_CHANGE_TIME_RELIABLE = os.name != 'nt'


def _identity(st):
    change_ns = st.st_ctime_ns if _CHANGE_TIME_RELIABLE else 0
    return st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, change_ns


def snapshot_source(path):
    """Read a stable file handle and verify that the pathname still names it."""
    try:
        with open(path, 'rb') as stream:
            before = os.fstat(stream.fileno())
            h = hashlib.sha256()
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                h.update(block)
            after = os.fstat(stream.fileno())
        current = os.stat(path)
    except OSError as exc:
        raise RuntimeError('Source indisponible pendant le contrôle : sortie rejetée') from exc
    if _identity(before) != _identity(after) or _identity(after) != _identity(current):
        raise RuntimeError('Source modifiée pendant le contrôle : sortie rejetée')
    return SourceSnapshot(*_identity(after), h.hexdigest())


def verify_source(path, expected):
    """Fail closed on changes even when file size and mtime are restored."""
    if snapshot_source(path) != expected:
        raise RuntimeError('Source modifiée pendant le traitement : sortie rejetée')
    return True
