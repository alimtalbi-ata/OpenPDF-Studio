"""UI-independent lifecycle for a single PDF task. Abdelhalim Talbi."""
from enum import Enum
class Phase(str, Enum):
    IDLE='idle'; RUNNING='running'; CANCELLING='cancelling'; SUCCEEDED='succeeded'; FAILED='failed'; CANCELLED='cancelled'
class TaskState:
    def __init__(self): self.phase=Phase.IDLE; self.handle=None
    def start(self, handle):
        if self.phase in (Phase.RUNNING,Phase.CANCELLING): raise RuntimeError('Task already active')
        self.handle=handle;self.phase=Phase.RUNNING
    def cancel(self):
        if self.phase==Phase.RUNNING:
            self.handle.cancel();self.phase=Phase.CANCELLING;return True
        return False
    def finish(self, result):
        if self.phase not in (Phase.RUNNING,Phase.CANCELLING): raise RuntimeError('No active task')
        cancelled=self.handle.cancelled()
        self.phase=Phase.CANCELLED if cancelled else Phase.FAILED if result.error else Phase.SUCCEEDED
        self.handle=None
        return self.phase
    @property
    def busy(self):return self.phase in (Phase.RUNNING,Phase.CANCELLING)
