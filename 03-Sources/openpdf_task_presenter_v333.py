"""V33.3 — Décision pure de présentation, sans dépendance Tk."""
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
        return CompletionView("error", str(getattr(result, "error", None) or "Échec du traitement"))
    if name != "SUCCEEDED":
        return CompletionView("warning", "Statut de traitement inconnu : " + name)
    if compression:
        if len(compression) != 2:
            return CompletionView("warning", "Informations de compression incomplètes")
        return CompletionView("compression", compression=(str(compression[0]), str(compression[1])))
    return CompletionView("success", str(getattr(result, "value", "")))
