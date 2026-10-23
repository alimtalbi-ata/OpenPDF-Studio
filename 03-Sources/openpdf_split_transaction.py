"""Crash-recoverable staged split with same-inode safe rollback.
Recovery must run under the same cooperative folder reservation as split.
Author: Abdelhalim Talbi. No multi-file atomic visibility guarantee.
"""
from pathlib import Path
from dataclasses import replace
import json
import os
import shutil
import tempfile
import stat
from pathlib import PureWindowsPath
from openpdf_page_service_v345 import split as legacy_split, _source
from openpdf_page_source_integrity_v435 import snapshot_source, verify_source
from openpdf_split_integrity_v449 import (file_sha256 as _sha256_file,
    valid_digest_list as _safe_digests, verify_staged as _verify_staged_digests)

PREFIX = ".openpdf-stage-"
JOURNAL = "transaction.json"
MAX_JOURNAL_BYTES = 256 * 1024
MAX_OUTPUTS = 20000
_RESERVED_WINDOWS = {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}

def _sync_dir(path):
    if os.name != "posix":
        return
    fd = os.open(str(path), os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)

def _journal(stage, names, state="prepared"):
    """Durably record SHA-256 of each output before changing recovery semantics.

    Schema 2 binds the phase marker to actual PDF bytes. Old schema 1 journals
    remain readable for recovery of previously interrupted releases.
    """
    if state not in ("prepared", "committed") or not _safe_names(names):
        raise ValueError("Invalid split journal state or names")
    tmp = stage / ".transaction.tmp"
    # Create first: a planted symlink must fail even if a staged file is absent.
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        digests = []
        for name in names:
            staged = stage / name
            if staged.is_symlink() or not staged.is_file():
                raise ValueError("Staged output absent or untrusted")
            digests.append(_sha256_file(staged))
        data = {"schema": 2, "state": state, "names": names, "sha256": digests}
        encoded = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        if len(encoded) > MAX_JOURNAL_BYTES:
            raise ValueError("Split journal exceeds safe size limit")
        with os.fdopen(fd, "wb") as f:
            fd = -1
            f.write(encoded)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, stage / JOURNAL)
        _sync_dir(stage)
        return digests
    except BaseException:
        if fd >= 0:
            os.close(fd)
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
        raise


def _safe_names(names):
    """Accept only portable, unambiguous, flat PDF basenames.

    A recovery journal is input data, not authority to delete arbitrary paths.
    Reject Windows aliases even when the recovery host runs Linux.
    """
    if not isinstance(names, list) or len(names) > MAX_OUTPUTS:
        return False
    folded = set()
    for name in names:
        if not isinstance(name, str) or not name or len(name) > 240:
            return False
        if name in (".", "..") or name.startswith(".") or name[-1] in " .":
            return False
        if any(ord(c) < 32 or ord(c) == 127 for c in name):
            return False
        if any(c in name for c in '/\\\x00<>:"|?*'):
            return False
        if Path(name).name != name or PureWindowsPath(name).name != name:
            return False
        if not name.lower().endswith('.pdf'):
            return False
        if name.split('.')[0].upper() in _RESERVED_WINDOWS:
            return False
        folded_name = name.casefold()
        if folded_name in folded:
            return False
        folded.add(folded_name)
    return True


def _trusted_stage(stage, journal):
    """Reject untrusted symlinked journals and foreign/unsafe stage entries."""
    try:
        stage_stat = stage.lstat()
        journal_stat = journal.lstat()
    except OSError:
        return False
    if not stat.S_ISDIR(stage_stat.st_mode) or not stat.S_ISREG(journal_stat.st_mode):
        return False
    if journal_stat.st_size > MAX_JOURNAL_BYTES:
        return False
    if os.name == 'posix':
        if stage_stat.st_uid != os.getuid() or journal_stat.st_uid != os.getuid():
            return False
        if stage_stat.st_mode & 0o022 or journal_stat.st_mode & 0o022:
            return False
    return True

def recover_transactions(folder):
    """Remove only outputs hard-linked to staged originals; never overwrite external files.
    Returns structured actions; malformed journals are quarantined for manual review.
    Caller must hold the cooperative destination reservation.
    """
    dest=Path(folder).resolve()
    if not dest.is_dir(): raise ValueError("Destination absente")
    report=[]
    for stage in sorted(dest.glob(PREFIX+"*")):
        if not stage.is_dir() or stage.is_symlink(): continue
        journal=stage/JOURNAL
        if not journal.exists() and not journal.is_symlink():
            report.append({"stage":stage.name,"status":"manual_review_missing_journal"})
            continue
        if not _trusted_stage(stage, journal):
            report.append({"stage":stage.name,"status":"manual_review_untrusted_journal"})
            continue
        try:
            data=json.loads(journal.read_text(encoding="utf-8"))
            names=data["names"]
            schema = data.get("schema")
            if (schema not in (1, 2) or data.get("state") not in ("prepared", "committed")
                    or not _safe_names(names)
                    or (schema == 2 and not _safe_digests(data.get("sha256"), names))):
                raise ValueError("invalid journal")
        except (ValueError,KeyError,TypeError,OSError):
            report.append({"stage":stage.name,"status":"manual_review_invalid_journal"})
            continue
        committed = data["state"] == "committed"
        conflict=False
        for name in names:
            target=dest/name
            staged=stage/name
            if staged.is_symlink() or not staged.is_file():
                conflict=True
            elif os.name == 'posix':
                staged_stat=staged.stat()
                if (staged_stat.st_uid != os.getuid() or staged_stat.st_mode & 0o022):
                    conflict=True
            if target.exists() or target.is_symlink():
                if (target.is_symlink() or not target.is_file() or not staged.is_file()
                        or staged.is_symlink() or not os.path.samefile(target,staged)):
                    conflict=True
            elif committed:
                # A durable commit cannot be silently accepted with missing outputs.
                conflict=True
        if conflict:
            report.append({"stage":stage.name,"status":
                "manual_review_committed_incomplete" if committed else "manual_review_foreign_target"})
            continue
        if schema == 2:
            try:
                _verify_staged_digests(stage, names, data["sha256"])
            except (OSError, RuntimeError):
                # Even matching hard-links can point to modified PDF bytes.
                # Never delete or finalize a transaction with failed integrity.
                report.append({"stage":stage.name,"status":"manual_review_integrity_mismatch"})
                continue
        if committed:
            # All hard-links match the staged originals: preserve the published
            # documents and only finalize removal of the crash residue.
            shutil.rmtree(stage)
            _sync_dir(dest)
            report.append({"stage":stage.name,"status":"committed","preserved":names})
            continue
        removed=[]
        for name in names:
            target=dest/name
            staged=stage/name
            if target.exists() and os.path.samefile(target,staged):
                target.unlink(); removed.append(name)
        _sync_dir(dest)
        shutil.rmtree(stage)
        _sync_dir(dest)
        report.append({"stage":stage.name,"status":"recovered","removed":removed})
    return report

def split_transaction(source,folder,chunk_size=1):
    src=_source(source)
    # Capture bytes and stable filesystem identity before staging any output.
    source_snapshot = snapshot_source(src)
    dest=Path(folder).resolve()
    if not dest.is_dir(): raise ValueError("Dossier de destination inexistant")
    # Never silently proceed over a crash residue: caller must recover explicitly.
    if any(p.is_dir() for p in dest.glob(PREFIX+"*")):
        raise RuntimeError("Transaction interrompue : lancer la récupération")
    stage=Path(tempfile.mkdtemp(prefix=PREFIX,dir=dest))
    published=[]
    try:
        receipt=legacy_split(src,stage,chunk_size)
        outputs=[Path(p) for p in receipt.outputs]
        names=[p.name for p in outputs]
        if not _safe_names(names): raise ValueError("Noms de sortie non valides")
        targets=[dest/name for name in names]
        if any(p.exists() or p.is_symlink() for p in targets): raise FileExistsError("Collision")
        for p in outputs:
            with p.open("r+b") as f: os.fsync(f.fileno())
        _sync_dir(stage)
        prepared_digests = _journal(stage,names)
        _verify_staged_digests(stage, names, prepared_digests)
        # Size/mtime alone cannot detect same-size edits with restored timestamps.
        verify_source(src, source_snapshot)
        for staged,target in zip(outputs,targets):
            os.link(staged,target)
            published.append(target)
            _sync_dir(dest)
        # Detect source changes that occur while links are being committed.
        # The rollback below removes only hard-links to our own staged files.
        verify_source(src, source_snapshot)
        # Verify output bytes again after publishing hard-links. A changed
        # staged inode would otherwise be certified by a fresh commit digest.
        _verify_staged_digests(stage, names, prepared_digests)
        # Recovery must never roll back a fully published, verified split.
        # Write the committed marker atomically and durably before stage cleanup.
        _journal(stage, names, state="committed")
        return replace(receipt,outputs=tuple(str(p) for p in targets))
    except BaseException:
        for p in reversed(published):
            if p.exists() and os.path.samefile(p,stage/p.name): p.unlink()
        _sync_dir(dest)
        raise
    finally:
        shutil.rmtree(stage,ignore_errors=True)
        _sync_dir(dest)
