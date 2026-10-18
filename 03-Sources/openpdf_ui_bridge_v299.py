"""V29.9: explicit UI routing preserving worker cancellation/progress. Abdelhalim Talbi."""
from types import MethodType
from openpdf_commands_v296 import PDFCommands
from openpdf_engine_v273 import merge_pdfs, extract_pages, compress_pdf

ROUTES = {merge_pdfs: 'merge', extract_pages: 'extract', compress_pdf: 'compress'}

def dispatch(commands, operation, args):
    method = ROUTES.get(operation)
    if method is None:
        raise ValueError('Fonction PDF non enregistrée')
    result = getattr(commands, method)(*args)
    return str(result.destination)

def connect(app):
    if getattr(app, '_v299_connected', False):
        return app
    original = app._run_pdf
    def routed(self, operation, *args):
        if operation in ROUTES:
            # The task runner injects progress/cancelled into this worker callable.
            # Creating the command instance inside the worker keeps callbacks task-local.
            def worker(*, progress=None, cancelled=None):
                commands = PDFCommands(progress=progress, cancelled=cancelled)
                return dispatch(commands, operation, args)
            return original(worker)
        return original(operation, *args)
    app._run_pdf = MethodType(routed, app)
    app._v299_connected = True
    return app
