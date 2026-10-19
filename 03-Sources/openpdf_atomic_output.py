"""Shared exclusive output publication primitive.

The source must be a completed temporary file on the destination volume.
A hard-link commit is atomic and fails when the destination exists, including
if another process creates it between validation and publication.
Author: Abdelhalim Talbi.
"""
import os
from pathlib import Path


def publish_exclusive(temporary, destination):
    """Publish without replacing an existing destination; return final Path.

    On volumes without hard-link support, fail closed rather than silently
    overwriting or downgrading atomicity. The caller owns temporary cleanup.
    """
    temporary = Path(temporary)
    destination = Path(destination)
    if not temporary.is_file() or temporary.stat().st_size == 0:
        raise ValueError("Sortie temporaire absente ou vide")
    if not destination.parent.is_dir():
        raise ValueError("Dossier de destination inexistant")
    if temporary.resolve() == destination.resolve():
        raise ValueError("Source temporaire et destination identiques")
    with temporary.open("r+b") as stream:
        stream.flush()
        os.fsync(stream.fileno())
    # Same-directory staging is required: linking across filesystems is not atomic.
    if temporary.parent.resolve() != destination.parent.resolve():
        raise ValueError('Le fichier temporaire doit etre dans le dossier de destination')
    try:
        os.link(temporary, destination)
    except FileExistsError:
        raise FileExistsError(f"Destination existante : {destination}") from None
    except OSError as exc:
        raise OSError(
            "Publication exclusive indisponible sur ce volume ; aucune sortie publiee"
        ) from exc
    return destination
