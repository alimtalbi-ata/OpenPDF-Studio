"""V27.1 compatible GUI entry point, with isolated engine and task runner available."""
from openpdf_windows_v270 import OpenPDFStudio as BaseStudio
from openpdf_tasks_v271 import TaskRunner

class OpenPDFStudio(BaseStudio):
    def __init__(self):
        super().__init__()
        self.title("OpenPDF Studio V27.1 — Abdelhalim Talbi")
        self.task_runner = TaskRunner()
        self.protocol("WM_DELETE_WINDOW", self._close_v271)

    def _close_v271(self):
        self.task_runner.pool.shutdown(wait=False, cancel_futures=True)
        self.destroy()

if __name__ == "__main__":
    OpenPDFStudio().mainloop()
