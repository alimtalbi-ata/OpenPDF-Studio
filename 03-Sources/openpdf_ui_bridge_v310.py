"""V31.0: unify legacy conversion button with transactional asynchronous controller."""
from pathlib import Path
from openpdf_ui_bridge_v303 import CONVERSIONS
from openpdf_ui_bridge_v309 import connect as connect_previous


def dispatch_selected(app, *, confirm_replace=None, warn=None):
    """Return True if queued, False if rejected, None for non-conversion legacy actions."""
    op = app.operation.get()
    if op not in CONVERSIONS:
        return None
    if getattr(app, 'busy', False) or getattr(app, '_v272_busy', False):
        return False
    if warn is None:
        from tkinter import messagebox
        warn = lambda title, message: messagebox.showwarning(title, message, parent=app)
    if confirm_replace is None:
        from tkinter import messagebox
        confirm_replace = lambda destination: messagebox.askyesno('Remplacement', 'Remplacer le fichier existant ?', parent=app)
    files = list(app.files)
    destination = str(app.destination.get()).strip()
    if len(files) != 1 or not destination:
        warn('Sélection', 'Choisissez un seul PDF et une destination.')
        return False
    source = Path(files[0]); target = Path(destination)
    _, extension = CONVERSIONS[op]
    if not source.is_file() or source.suffix.lower() != '.pdf':
        warn('Source', 'Le fichier PDF source est introuvable ou invalide.')
        return False
    if target.suffix.lower() != '.' + extension:
        warn('Destination', 'Extension attendue : .' + extension)
        return False
    if source.resolve() == target.resolve():
        warn('Destination', 'Source et destination doivent être différentes.')
        return False
    if not target.parent.is_dir():
        warn('Destination', 'Le dossier de destination est introuvable.')
        return False
    if target.exists() and not confirm_replace(target):
        return False
    operation, _ = CONVERSIONS[op]
    app._run_pdf(operation, str(source), str(target))
    return True


def connect(app):
    connect_previous(app)
    if getattr(app, '_v310_connected', False):
        return app
    app._v310_connected = True
    return app
