"""V549 lexical destination-path guard for PDF output and recovery paths.

Rejects symbolic links and Windows junctions in every existing path component
before canonicalization. This is a preflight check, not an OS-level guarantee
against a hostile process replacing an ancestor after the check.
Author: Abdelhalim Talbi.
"""
from pathlib import Path
import stat


_LINK_ERROR = "Destination via lien symbolique ou jonction interdite"


def _is_link_or_junction(path):
    try:
        if path.is_symlink():
            return True
        is_junction = getattr(path, "is_junction", None)
        return bool(is_junction()) if callable(is_junction) else False
    except OSError as exc:
        raise ValueError("Destination inaccessible") from exc


def guard_destination_path(path, *, directory=False, allow_existing=False):
    """Validate the lexical path before normalizing any component.

    Existing parent directories must be real directories. For a file output,
    only the final component may be missing. When allow_existing=True, an
    existing regular file is returned so the caller can preserve its own
    reservation and no-overwrite semantics. Directory targets must exist.
    Path.resolve() is deliberately never called.
    """
    try:
        candidate = Path(path).expanduser()
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        if not candidate.anchor:
            raise ValueError("Destination invalide")
        if not directory and candidate.name in ("", ".", ".."):
            raise ValueError("Fichier de destination invalide")

        current = Path(candidate.anchor)
        if _is_link_or_junction(current):
            raise ValueError(_LINK_ERROR)
        parts = candidate.parts[1:]
        for index, component in enumerate(parts):
            if component in ("", "."):
                continue
            if component == "..":
                current = current.parent
                continue

            current = current / component
            if _is_link_or_junction(current):
                if index == len(parts) - 1 and not directory:
                    # Preserve the legacy file-output contract; linked directory
                    # targets are invalid destinations, not file-exists conflicts.
                    raise FileExistsError("Destination lien symbolique interdite")
                raise ValueError(_LINK_ERROR)
            try:
                info = current.lstat()
            except FileNotFoundError as exc:
                remainder = [item for item in parts[index + 1:] if item not in ("", ".")]
                if remainder:
                    raise ValueError("Dossier parent destination introuvable") from exc
                continue
            except (OSError, ValueError) as exc:
                raise ValueError("Destination inaccessible") from exc

            if stat.S_ISLNK(info.st_mode):
                raise ValueError(_LINK_ERROR)
            remainder = [item for item in parts[index + 1:] if item not in ("", ".")]
            if remainder and not stat.S_ISDIR(info.st_mode):
                raise ValueError("Composant parent destination non répertoire")

        try:
            info = current.lstat()
            exists = True
        except FileNotFoundError:
            info = None
            exists = False
        except (OSError, ValueError) as exc:
            raise ValueError("Destination inaccessible") from exc

        if exists and (_is_link_or_junction(current) or stat.S_ISLNK(info.st_mode)):
            raise ValueError(_LINK_ERROR)

        if directory:
            if not exists or not stat.S_ISDIR(info.st_mode):
                raise ValueError("Dossier de destination inexistant ou invalide")
            return current

        if exists and not stat.S_ISREG(info.st_mode):
            raise ValueError("Fichier de destination invalide")
        if not current.name or current == current.parent:
            raise ValueError("Fichier de destination invalide")
        try:
            parent_info = current.parent.lstat()
        except (OSError, ValueError) as exc:
            raise ValueError("Dossier parent destination introuvable") from exc
        if _is_link_or_junction(current.parent) or stat.S_ISLNK(parent_info.st_mode):
            raise ValueError(_LINK_ERROR)
        if not stat.S_ISDIR(parent_info.st_mode):
            raise ValueError("Dossier de destination inexistant ou invalide")
        if exists and not allow_existing:
            raise FileExistsError("Destination existante")
        return current
    except FileExistsError:
        raise
    except ValueError:
        raise
    except (OSError, RuntimeError, TypeError) as exc:
        raise ValueError("Destination invalide ou inaccessible") from exc
