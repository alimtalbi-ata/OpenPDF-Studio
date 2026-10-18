"""Stable job lifecycle, independent of Tkinter. Author: Abdelhalim Talbi."""
from dataclasses import dataclass
from uuid import uuid4

@dataclass
class JobState:
    active_id: str | None = None
    last_result: str | None = None
    def start(self, operation: str) -> str:
        if self.active_id is not None:
            raise RuntimeError('Un traitement est déjà en cours')
        if not operation:
            raise ValueError('Opération obligatoire')
        self.active_id = uuid4().hex
        self.last_result = None
        return self.active_id
    def finish(self, job_id: str, outcome: str) -> bool:
        if not job_id or job_id != self.active_id:
            return False
        if outcome not in ('success', 'error'):
            raise ValueError('Résultat inconnu')
        self.active_id = None
        self.last_result = outcome
        return True
