"""V34.0 — pure UI operation controller, independent from Tkinter."""
from dataclasses import dataclass
from enum import Enum

class OperationKind(str, Enum):
    COMPRESS = "compress"
    MERGE = "merge"
    SPLIT = "split"
    CONVERT = "convert"
    OTHER = "other"

@dataclass(frozen=True)
class OperationRequest:
    kind: OperationKind
    source: str
    destination: str
    operation_name: str

@dataclass(frozen=True)
class OperationDecision:
    accepted: bool
    reason: str = ""

def classify_operation(operation):
    name = getattr(operation, "__name__", "")
    if name in {"compress_with_profile", "compress_with_receipt", "compression_with_report"}:
        return OperationKind.COMPRESS
    if "merge" in name or "fusion" in name:
        return OperationKind.MERGE
    if "split" in name or "decoup" in name:
        return OperationKind.SPLIT
    if "convert" in name or "export" in name:
        return OperationKind.CONVERT
    return OperationKind.OTHER

def validate_request(request, busy=False):
    if busy:
        return OperationDecision(False, "Une opération est déjà en cours")
    if request.kind == OperationKind.COMPRESS:
        from pathlib import Path
        if not request.source or not request.destination:
            return OperationDecision(False, "Chemins de compression manquants")
        if Path(request.source).resolve() == Path(request.destination).resolve():
            return OperationDecision(False, "La source et la destination doivent être distinctes")
    return OperationDecision(True)
