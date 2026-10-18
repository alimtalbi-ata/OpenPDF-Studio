"""Adaptateur UI/moteur V29.7 — Abdelhalim Talbi.

Raccorde les trois actions historiques au contrôleur sans changer les dialogues,
le task runner ni la gestion des erreurs existante.
"""
from types import MethodType
from openpdf_commands_v296 import PDFCommands

OPERATIONS = frozenset(('merge_pdfs', 'extract_pages', 'compress_pdf'))

def dispatch(commands, operation, args):
    name = getattr(operation, '__name__', '')
    if name == 'merge_pdfs':
        result = commands.merge(*args)
    elif name == 'extract_pages':
        result = commands.extract(*args)
    elif name == 'compress_pdf':
        result = commands.compress(*args)
    else:
        raise ValueError('Opération non prise en charge : ' + name)
    return str(result.destination)

def connect(app):
    """Installe un adaptateur sur cette instance uniquement; idempotent."""
    if getattr(app, '_v297_connected', False):
        return app
    original = app._run_pdf
    commands = PDFCommands()
    def routed(self, operation, *args):
        if getattr(operation, '__name__', '') in OPERATIONS:
            return original(lambda: dispatch(commands, operation, args))
        return original(operation, *args)
    app.pdf_commands = commands
    app._run_pdf = MethodType(routed, app)
    app._v297_connected = True
    return app
