"""Pre/post task output provenance. Conservative: ambiguous results are not confirmed."""
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class FileFingerprint:
    size: int
    mtime_ns: int
    inode: int

def fingerprint(path):
    try:
        s = Path(path).stat()
        return FileFingerprint(s.st_size, s.st_mtime_ns, s.st_ino) if Path(path).is_file() else None
    except OSError:
        return None

def compression_publication(before, destination, result_value):
    """True only when output exists and differs from pre-task snapshot.
    Explicit 'no gain' engine status always rejects publication.
    """
    value = str(result_value or '')
    if value.startswith('Aucun gain') or 'Aucun fichier de sortie modifié' in value:
        return False, 'Compression sans gain : aucun nouveau fichier publié.'
    after = fingerprint(destination)
    if after is None or after.size <= 0:
        return False, 'Sortie absente ou vide.'
    if before is not None and before == after:
        return False, 'Sortie inchangée depuis le lancement (fichier potentiellement ancien).'
    return True, 'Sortie produite et modifiée pendant le traitement.'
