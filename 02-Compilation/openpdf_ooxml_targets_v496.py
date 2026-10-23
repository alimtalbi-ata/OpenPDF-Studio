"""Validate internal OOXML relationship destinations against the package index.

V49.6. Author: Abdelhalim Talbi. Static validation, not malware scanning.
"""
from __future__ import annotations

from pathlib import PurePosixPath
import re
from urllib.parse import unquote, urlsplit

_ENCODED_SEPARATOR = re.compile(r"%(?:2f|5c|00)", re.IGNORECASE)
_ENCODED_DOT = re.compile(r"%2e", re.IGNORECASE)
_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def validate_internal_target(rels_part: str, target: str, members: set[str]) -> str:
    """Resolve a package-local relationship and require a present regular part."""
    if not isinstance(target, str) or not target or not isinstance(rels_part, str):
        raise ValueError("Invalid OOXML relationship target")
    if any(ord(c) < 32 or ord(c) == 127 for c in target):
        raise ValueError("Control character in OOXML relationship")
    if ("\\" in target or target.startswith("/") or _SCHEME.match(target)
            or _ENCODED_SEPARATOR.search(target) or _ENCODED_DOT.search(target)):
        raise ValueError("External or unsafe OOXML relationship")
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        raise ValueError("External or ambiguous OOXML relationship")
    decoded = unquote(parsed.path)
    if not decoded or decoded.endswith("/") or "\\" in decoded:
        raise ValueError("Invalid OOXML relationship target")
    relpath = PurePosixPath(rels_part)
    if relpath.name == ".rels" and relpath.parent == PurePosixPath("_rels"):
        base = []
    elif relpath.parent.name == "_rels" and relpath.name.endswith(".rels"):
        base = list(relpath.parent.parent.parts)
    else:
        raise ValueError("Invalid OOXML relationship part location")
    parts = base
    for part in decoded.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if not parts:
                raise ValueError("OOXML relationship escapes package root")
            parts.pop()
        else:
            if part.rstrip(" .") != part or ":" in part:
                raise ValueError("Unsafe OOXML relationship component")
            parts.append(part)
    resolved = "/".join(parts)
    if not resolved or resolved not in members:
        raise ValueError("OOXML relationship target missing from package: " + resolved)
    return resolved
