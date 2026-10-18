"""Routage sûr des actions UI vers le moteur PDF — V29.8, Abdelhalim Talbi.

Seules les fonctions explicitement enregistrées sont routées : aucune collision
possible avec une fonction tierce portant le même nom.
"""
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
    if getattr(app, '_v298_connected', False):
        return app
    original = app._run_pdf
    commands = PDFCommands()
    def routed(self, operation, *args):
        if operation in ROUTES:
            return original(lambda: dispatch(commands, operation, args))
        return original(operation, *args)
    app.pdf_commands = commands
    app._run_pdf = MethodType(routed, app)
    app._v298_connected = True
    return app
