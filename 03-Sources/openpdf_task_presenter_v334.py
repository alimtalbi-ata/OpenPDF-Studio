"""V33.4: validation explicite du resultat du travail avant affichage."""
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class CompletionView:
    kind: str
    message: str = ""
    compression: tuple | None = None

def completion_view(phase, result, compression=None):
    name = getattr(phase, "name", str(phase)).upper()
    if name == "CANCELLED":
        return CompletionView("cancelled")
    if name == "FAILED":
        return CompletionView("error", str(getattr(result, "error", None) or "Echec du traitement"))
    if name != "SUCCEEDED":
        return CompletionView("warning", "Statut non confirme : " + name)
    if getattr(result, "error", None):
        return CompletionView("error", str(result.error))
    if compression:
        if len(compression) != 2:
            return CompletionView("warning", "Informations de compression incompletes")
        source, destination = map(Path, compression)
        if source.resolve() == destination.resolve():
            return CompletionView("error", "Source et destination identiques")
        if not source.is_file() or not destination.is_file() or destination.stat().st_size == 0:
            return CompletionView("warning", "Fichier de sortie absent ou vide")
        return CompletionView("compression", compression=(str(source), str(destination)))
    value = getattr(result, "value", None)
    if value is None:
        return CompletionView("warning", "Aucun resultat confirme")
    return CompletionView("success", str(value))
