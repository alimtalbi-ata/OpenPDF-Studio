"""Thread-safe cancellation and progress, no Tk calls from workers. Abdelhalim Talbi."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from threading import Event, Lock

@dataclass(frozen=True)
class TaskResult:
    value: object = None
    error: Exception = None

class TaskHandle:
    def __init__(self):
        self._cancel=Event();self._lock=Lock();self._progress=0.0;self.future=None
    def cancel(self): self._cancel.set()
    def cancelled(self): return self._cancel.is_set()
    def set_progress(self,value):
        with self._lock: self._progress=max(0.0,min(1.0,float(value)))
    @property
    def progress(self):
        with self._lock: return self._progress

class TaskRunner:
    def __init__(self,workers=2): self.pool=ThreadPoolExecutor(max_workers=workers,thread_name_prefix='openpdf')
    def submit(self,operation,*args,**kwargs):
        handle=TaskHandle()
        def work():
            try:
                return TaskResult(value=operation(*args,progress=handle.set_progress,cancelled=handle.cancelled,**kwargs))
            except Exception as exc: return TaskResult(error=exc)
        handle.future=self.pool.submit(work)
        return handle
    def shutdown(self): self.pool.shutdown(wait=False,cancel_futures=True)
