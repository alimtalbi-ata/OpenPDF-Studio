"""Bounded DOCX validation and safe archive destination selection.

OpenPDF Studio V49.4. Author: Abdelhalim Talbi.
This is an input-safety check, not a digital signature or Windows qualification.
"""
from __future__ import annotations

import io
import os
from pathlib import Path
import stat
import unicodedata
import zipfile

MAX_DOCX_BYTES = 32 * 1024 * 1024
MAX_DOCX_ENTRIES = 4096
MAX_DOCX_TOTAL = 128 * 1024 * 1024
MAX_DOCX_MEMBER = 32 * 1024 * 1024
MAX_DOCX_RATIO = 500


def validate_docx_bytes(data: bytes) -> dict:
    """Inspect OOXML structure before bounded CRC validation of each part.

    Refuses nested ZIP bombs, traversal, Windows case aliases, encrypted parts,
    symlink entries, and missing main document. All size limits are explicit.
    """
    if not isinstance(data, bytes) or len(data) > MAX_DOCX_BYTES:
        raise ValueError("DOCX exceeds compressed size budget")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            infos = archive.infolist()
            if len(infos) > MAX_DOCX_ENTRIES:
                raise ValueError("DOCX exceeds entry budget")
            names = set()
            folded = set()
            total = 0
            for info in infos:
                name = info.filename
                if (not name or name.startswith(("/", "\\")) or "\\" in name
                        or any(c in name for c in ':<>"?*|')
                        or any(ord(c) < 32 for c in name)):
                    raise ValueError("Unsafe DOCX member path")
                parts = name.rstrip("/").split("/")
                if any(not part or part in (".", "..") or part.rstrip(" .") != part
                       for part in parts):
                    raise ValueError("Unsafe DOCX member path")
                if unicodedata.normalize("NFKC", name) != name:
                    raise ValueError("Noncanonical DOCX member path")
                key = name.rstrip("/").casefold()
                if key in folded:
                    raise ValueError("Duplicate DOCX member")
                folded.add(key)
                names.add(name)
                mode = stat.S_IFMT(info.external_attr >> 16)
                if mode not in (0, stat.S_IFREG, stat.S_IFDIR):
                    raise ValueError("Nonregular DOCX member")
                if (info.flag_bits & 0x1 or info.compress_type not in
                        (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)):
                    raise ValueError("Encrypted or unsupported DOCX member")
                if info.is_dir():
                    if info.file_size:
                        raise ValueError("Nonempty DOCX directory")
                    continue
                total += info.file_size
                if (info.file_size > MAX_DOCX_MEMBER or total > MAX_DOCX_TOTAL or
                        (info.file_size and (not info.compress_size or
                         info.file_size / info.compress_size > MAX_DOCX_RATIO))):
                    raise ValueError("DOCX decompression budget exceeded")
            if "word/document.xml" not in names:
                raise ValueError("DOCX missing word/document.xml")
            # CRC-check all members, but only after checking cumulative metadata.
            for info in infos:
                if info.is_dir():
                    continue
                with archive.open(info) as part:
                    for _ in iter(lambda: part.read(1024 * 1024), b""):
                        pass
            return {"parts": len(infos), "uncompressed_bytes": total}
    except (zipfile.BadZipFile, RuntimeError, EOFError, OSError) as exc:
        raise ValueError("Invalid DOCX container") from exc


def safe_output_path(output: str | Path) -> Path:
    """Canonicalize the parent only; never follow a final output symlink.

    os.replace(temp, path) replaces the directory entry, not the link target.
    Caller must recheck immediately before publishing for policy consistency.
    """
    raw = Path(output)
    if not raw.name or raw.name in (".", ".."):
        raise ValueError("Invalid output filename")
    parent = raw.parent.resolve(strict=True)
    if not parent.is_dir():
        raise ValueError("Output parent is not a directory")
    target = parent / raw.name
    if target.is_symlink():
        raise ValueError("Output must not be a symlink")
    if target.exists() and not target.is_file():
        raise ValueError("Output must be a regular file")
    return target
