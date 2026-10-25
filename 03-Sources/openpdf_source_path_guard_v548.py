"""V548 source-path chain guard for PDF inputs on Windows and POSIX.

Reject symbolic links and Windows junctions in every existing lexical path
component before canonicalization. This is a preflight guard, not an OS-level
guarantee against a hostile process replacing an ancestor after the check.
Author: Abdelhalim Talbi.
"""
from pathlib import Path
import stat


_LINK_ERROR = "Source PDF via lien symbolique interdit"


def _is_link_or_junction(path):
    """Inspect the path itself without resolving it."""
    try:
        if path.is_symlink():
            return True
        is_junction = getattr(path, "is_junction", None)
        return bool(is_junction()) if callable(is_junction) else False
    except OSError as exc:
        raise ValueError("Chemin source PDF inaccessible") from exc


def guard_pdf_source_path(path):
    """Return a lexical absolute PDF path only if no component is a link.

    Components are checked in their original order, before applying '..'.
    Consequently a path such as link/../file cannot conceal the link by
    normalization. The routine deliberately does not call Path.resolve().
    """
    try:
        candidate = Path(path).expanduser()
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        if not candidate.anchor:
            raise ValueError("Source PDF invalide")

        current = Path(candidate.anchor)
        if _is_link_or_junction(current):
            raise ValueError(_LINK_ERROR)

        for component in candidate.parts[1:]:
            if component in ("", "."):
                continue
            if component == "..":
                current = current.parent
                continue

            current = current / component
            if _is_link_or_junction(current):
                raise ValueError(_LINK_ERROR)
            try:
                info = current.lstat()
            except (OSError, ValueError) as exc:
                raise ValueError("Source PDF inaccessible ou introuvable") from exc
            if stat.S_ISLNK(info.st_mode):
                raise ValueError(_LINK_ERROR)

        # Recheck the final lexical component and require a real regular PDF.
        if _is_link_or_junction(current):
            raise ValueError(_LINK_ERROR)
        try:
            info = current.lstat()
        except (OSError, ValueError) as exc:
            raise ValueError("Source PDF inaccessible ou introuvable") from exc
        if stat.S_ISLNK(info.st_mode):
            raise ValueError(_LINK_ERROR)
        if not stat.S_ISREG(info.st_mode) or current.suffix.lower() != ".pdf":
            raise ValueError("Source PDF invalide")
        return current
    except ValueError:
        raise
    except (OSError, RuntimeError, TypeError) as exc:
        raise ValueError("Source PDF invalide ou inaccessible") from exc
