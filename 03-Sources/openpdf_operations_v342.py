"""Stable, explicit operation registry; no Tkinter dependency."""
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable

class OperationKind(str, Enum):
    COMPRESS="compress"
    MERGE="merge"
    SPLIT="split"
    CONVERT="convert"
    OTHER="other"

@dataclass(frozen=True)
class OperationSpec:
    operation_id: str
    kind: OperationKind
    requires_distinct_paths: bool = False

SPECS = {
    "pdf.compress": OperationSpec("pdf.compress", OperationKind.COMPRESS, True),
    "pdf.merge": OperationSpec("pdf.merge", OperationKind.MERGE),
    "pdf.split": OperationSpec("pdf.split", OperationKind.SPLIT),
    "pdf.convert": OperationSpec("pdf.convert", OperationKind.CONVERT),
}

class OperationRegistry:
    def __init__(self):
        self._operations = {}
    def register(self, operation_id: str, func: Callable):
        if operation_id not in SPECS: raise KeyError(f"Opération inconnue : {operation_id}")
        if not callable(func): raise TypeError("Une fonction exécutable est requise")
        if operation_id in self._operations: raise ValueError("Opération déjà enregistrée")
        self._operations[operation_id] = func
    def resolve(self, operation_id: str):
        return self._operations[operation_id]
    def describe(self, operation_id: str):
        return SPECS[operation_id]
    def available(self):
        return tuple(sorted(self._operations))

@dataclass(frozen=True)
class DispatchDecision:
    accepted: bool
    reason: str = ""

class OperationController:
    def __init__(self, registry: OperationRegistry):
        self.registry=registry
        self._busy=False
    @property
    def busy(self): return self._busy
    def validate(self, operation_id: str, source=None, destination=None):
        if self._busy: return DispatchDecision(False, "Une opération est déjà en cours")
        if operation_id not in self.registry.available():
            return DispatchDecision(False, "Opération non enregistrée")
        spec=self.registry.describe(operation_id)
        if spec.requires_distinct_paths:
            if not source or not destination: return DispatchDecision(False, "Chemins requis")
            if Path(source).resolve()==Path(destination).resolve():
                return DispatchDecision(False, "Source et destination identiques")
        return DispatchDecision(True)
    def begin(self, operation_id, source=None, destination=None):
        decision=self.validate(operation_id,source,destination)
        if decision.accepted:self._busy=True
        return decision
    def finish(self):
        self._busy=False
