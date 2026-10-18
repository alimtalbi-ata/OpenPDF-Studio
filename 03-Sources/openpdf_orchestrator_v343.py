"""Single-task orchestration, independent from Tkinter. Author: Abdelhalim Talbi."""
from dataclasses import dataclass
from enum import Enum
from threading import RLock
from uuid import uuid4
from openpdf_operations_v342 import OperationController, OperationRegistry

class JobPhase(str, Enum):
    RUNNING="running"
    CANCELLING="cancelling"
    SUCCEEDED="succeeded"
    FAILED="failed"
    CANCELLED="cancelled"

@dataclass(frozen=True)
class JobSnapshot:
    job_id: str
    operation_id: str
    phase: JobPhase
    error: str = ""

class JobOrchestrator:
    def __init__(self, registry=None):
        self.registry=registry if registry is not None else OperationRegistry()
        self.controller=OperationController(self.registry)
        self._lock=RLock()
        self._active=None
        self._last=None
    @property
    def active(self):
        with self._lock:return self._active
    @property
    def last(self):
        with self._lock:return self._last
    def submit(self, operation_id, source=None, destination=None):
        with self._lock:
            decision=self.controller.begin(operation_id,source,destination)
            if not decision.accepted: return decision,None
            self._active=JobSnapshot(uuid4().hex,operation_id,JobPhase.RUNNING)
            return decision,self._active
    def cancelling(self, job_id):
        with self._lock:
            if self._active is None or self._active.job_id!=job_id:return False
            if self._active.phase!=JobPhase.RUNNING:return False
            self._active=JobSnapshot(job_id,self._active.operation_id,JobPhase.CANCELLING)
            return True
    def complete(self, job_id, phase, error=""):
        with self._lock:
            if self._active is None or self._active.job_id!=job_id:return None
            phase=JobPhase(phase)
            if phase not in (JobPhase.SUCCEEDED,JobPhase.FAILED,JobPhase.CANCELLED):
                raise ValueError("Terminal phase required")
            self._last=JobSnapshot(job_id,self._active.operation_id,phase,str(error))
            self._active=None
            self.controller.finish()
            return self._last
    def abort_submission(self,job_id,error=""):
        return self.complete(job_id,JobPhase.FAILED,error)
