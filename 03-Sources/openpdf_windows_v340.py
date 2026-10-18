"""V34.0 — initial controller extraction with backwards-compatible UI."""
from openpdf_windows_v339 import OpenPDFStudio as Previous
from openpdf_controller_v340 import OperationRequest, classify_operation, validate_request, OperationKind

class OpenPDFStudio(Previous):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title('OpenPDF Studio V34.0 — Abdelhalim Talbi')

    def _run_pdf(self, operation, *args):
        kind = classify_operation(operation)
        if kind == OperationKind.COMPRESS and len(args) >= 2:
            request = OperationRequest(kind, str(args[0]), str(args[1]), getattr(operation, '__name__', ''))
            decision = validate_request(request, busy=bool(getattr(self._task_state, 'busy', False)))
            if not decision.accepted and not getattr(self._task_state, 'busy', False):
                from tkinter import messagebox
                messagebox.showwarning('Compression non lancée', decision.reason, parent=self)
                return None
        return super()._run_pdf(operation, *args)

if __name__ == '__main__':
    OpenPDFStudio().mainloop()
