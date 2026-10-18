"""V31.3: guided Word export and safe, predictable action routing.
Author: Abdelhalim Talbi.
"""
from pathlib import Path
from openpdf_essentials_v312 import connect as connect_previous, safe_launch
from openpdf_ui_bridge_v310 import dispatch_selected

WORD_OPERATION = 'PDF vers Word (texte)'

def prepare_word(app, source, destination, *, confirm_replace=None, warn=None):
    """Validate selections through the existing V31.0 gate, never call converter directly."""
    if getattr(app, 'busy', False) or getattr(app, '_v272_busy', False):
        return False
    if not source or not destination:
        return False
    app.files = [str(source)]
    app.operation.set(WORD_OPERATION)
    app.destination.set(str(destination))
    return dispatch_selected(app, confirm_replace=confirm_replace, warn=warn)

def suggest_destination(source):
    if not source:
        raise ValueError('Source manquante')
    return str(Path(source).with_suffix('.docx'))

def guided_word(app, *, ask_source=None, ask_destination=None, confirm_replace=None, warn=None):
    """Four steps: select PDF, propose DOCX, validate, launch via transactional controller."""
    if getattr(app, 'busy', False) or getattr(app, '_v272_busy', False):
        return False
    if ask_source is None or ask_destination is None:
        from tkinter import filedialog
        ask_source = ask_source or (lambda: filedialog.askopenfilename(parent=app, title='1/3 — Choisir le PDF', filetypes=[('PDF', '*.pdf')]))
        ask_destination = ask_destination or (lambda suggested: filedialog.asksaveasfilename(parent=app, title='2/3 — Enregistrer le Word', initialfile=Path(suggested).name, initialdir=str(Path(suggested).parent), defaultextension='.docx', filetypes=[('Word', '*.docx')]))
    source = ask_source()
    if not source:
        return False
    destination = ask_destination(suggest_destination(source))
    if not destination:
        return False
    return prepare_word(app, source, destination, confirm_replace=confirm_replace, warn=warn)

def launch_common(app, action):
    if action == WORD_OPERATION:
        return guided_word(app)
    return safe_launch(app, action)

def connect(app):
    connect_previous(app)
    if getattr(app, '_v313_connected', False):
        return app
    app._v313_connected = True
    import tkinter as tk
    from tkinter import ttk
    if not isinstance(app, tk.Tk):
        return app
    panel = getattr(app, '_v311_essentials', None)
    if panel is None:
        return app
    # Replace only the Word button callback. All other actions preserve existing paths.
    for child in panel.winfo_children():
        if isinstance(child, ttk.Button) and child.cget('text').startswith('Vers Word'):
            child.configure(command=lambda: guided_word(app))
    app.bind('<Control-Shift-w>', lambda event: guided_word(app))
    return app
