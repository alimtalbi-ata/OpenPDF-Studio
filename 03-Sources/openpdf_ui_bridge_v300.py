"""V30.0 safe UI command dispatch. Abdelhalim Talbi."""
from types import MethodType
from openpdf_commands_v296 import PDFCommands
from openpdf_engine_v273 import merge_pdfs, extract_pages, compress_pdf
from openpdf_output_policy_v300 import validate_output

ROUTES = {merge_pdfs: 'merge', extract_pages: 'extract', compress_pdf: 'compress'}

def dispatch(commands, operation, args):
    method = ROUTES.get(operation)
    if method is None:
        raise ValueError('Fonction PDF non enregistrée')
    if method == 'merge':
        sources, dest = args
        # Preserve generators: materialize once before validation and dispatch.
        sources = list(sources)
        validate_output(sources, dest)
        args = (sources, dest)
    elif method in ('extract', 'compress'):
        validate_output([args[0]], args[1])
    result = getattr(commands, method)(*args)
    return str(result.destination)

def connect(app):
    if getattr(app, '_v300_connected', False):
        return app
    original = app._run_pdf
    def routed(self, operation, *args):
        if operation in ROUTES:
            def worker(*, progress=None, cancelled=None):
                commands = PDFCommands(progress=progress, cancelled=cancelled)
                return dispatch(commands, operation, args)
            return original(worker)
        return original(operation, *args)
    app._run_pdf = MethodType(routed, app)
    app._v300_connected = True
    return app
