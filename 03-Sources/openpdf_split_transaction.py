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
from openpdf_page_service_v345 import split as legacy_split, _source_identity, _source

PREFIX = ".openpdf-stage-"
JOURNAL = "transaction.json"

def _sync_dir(path):
    if os.name != "posix":
        return
    fd = os.open(str(path), os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)

def _journal(stage, names):
    tmp = stage / ".transaction.tmp"
    with tmp.open("w", encoding="utf-8") as f:
        json.dump({"schema":1, "state":"prepared", "names":names}, f)
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp, stage / JOURNAL)
    _sync_dir(stage)

def _safe_names(names):
    return isinstance(names,list) and len(names)==len(set(names)) and all(
        isinstance(n,str) and n not in ("", ".", "..") and Path(n).name == n
        and not n.startswith(".") for n in names)

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
        if not journal.is_file():
            report.append({"stage":stage.name,"status":"manual_review_missing_journal"})
            continue
        try:
            data=json.loads(journal.read_text(encoding="utf-8"))
            names=data["names"]
            if data.get("schema") != 1 or not _safe_names(names): raise ValueError("invalid journal")
        except (ValueError,KeyError,TypeError,OSError):
            report.append({"stage":stage.name,"status":"manual_review_invalid_journal"})
            continue
        conflict=False
        for name in names:
            target=dest/name
            staged=stage/name
            if target.exists() or target.is_symlink():
                if not staged.is_file() or staged.is_symlink() or not os.path.samefile(target,staged):
                    conflict=True
        if conflict:
            report.append({"stage":stage.name,"status":"manual_review_foreign_target"})
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
    identity=_source_identity(src)
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
        _journal(stage,names)
        if _source_identity(src)!=identity:
            raise RuntimeError('Source modifiée pendant le découpage : sortie rejetée')
        for staged,target in zip(outputs,targets):
            os.link(staged,target)
            published.append(target)
            _sync_dir(dest)
        return replace(receipt,outputs=tuple(str(p) for p in targets))
    except BaseException:
        for p in reversed(published):
            if p.exists() and os.path.samefile(p,stage/p.name): p.unlink()
        _sync_dir(dest)
        raise
    finally:
        shutil.rmtree(stage,ignore_errors=True)
        _sync_dir(dest)
