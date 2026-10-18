"""V33.9: preserve compression context across worker adapter substitution."""
from openpdf_windows_v338 import OpenPDFStudio as Previous
from openpdf_transaction_v338 import compress_with_receipt

def resolve_operation(operation):
    """Return worker function and whether this is a compression task."""
    name = getattr(operation, '__name__', '')
    if name == 'compress_with_profile':
        return compress_with_receipt, True
    if operation is compress_with_receipt:
        return operation, True
    return operation, False

class OpenPDFStudio(Previous):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title('OpenPDF Studio V33.9 — Abdelhalim Talbi')

    def _run_pdf(self, operation, *args):
        # The V33.8 adapter changes the operation name before V33.1 can
        # register its source/destination. Restore context only if accepted.
        worker, compression = resolve_operation(operation)
        busy = bool(getattr(self._task_state, 'busy', False))
        outcome = super()._run_pdf(operation, *args)
        if compression and not busy and len(args) >= 2:
            self._v331_compression = (str(args[0]), str(args[1]))
        return outcome

if __name__ == '__main__':
    OpenPDFStudio().mainloop()
