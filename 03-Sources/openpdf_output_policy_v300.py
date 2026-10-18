"""Safe output-path policy for PDF operations. Abdelhalim Talbi."""
from pathlib import Path

class OutputConflictError(ValueError):
    pass

def validate_output(sources, destination):
    """Reject a destination aliasing any input (including symlinks)."""
    inputs = [Path(p).expanduser().resolve(strict=False) for p in sources]
    output = Path(destination).expanduser().resolve(strict=False)
    if output in inputs:
        raise OutputConflictError("Le fichier de sortie ne peut pas remplacer un fichier source")
    if not output.parent.is_dir():
        raise OutputConflictError("Le dossier de destination n'existe pas")
    if output.exists() and not output.is_file():
        raise OutputConflictError("La destination n'est pas un fichier")
    return output
