"""Worker execution separated from Tk main thread. Author: Abdelhalim Talbi."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

@dataclass(frozen=True)
class TaskResult:
    value: object = None
    error: Exception = None

class TaskRunner:
    def __init__(self, workers=2):
        self.pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="openpdf")

    def submit(self, operation, *args, **kwargs):
        """Returns Future[TaskResult]; UI must poll future from its main thread."""
        def execute():
            try:
                return TaskResult(value=operation(*args, **kwargs))
            except Exception as exc:
                return TaskResult(error=exc)
        return self.pool.submit(execute)

    def shutdown(self):
        self.pool.shutdown(wait=True, cancel_futures=True)
