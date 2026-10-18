"""V30.3: direct, consistent quick actions for all conversions.
Author: Abdelhalim Talbi.
"""
from pathlib import Path
from openpdf_ui_bridge_v302 import connect as connect_previous, ACTIONS
from openpdf_core_v260 import pdf_to_docx, pdf_to_xlsx, pdf_to_pptx, extract_text

CONVERSIONS = {
    'PDF vers Word (texte)': (pdf_to_docx, 'docx'),
    'PDF vers Excel (lignes)': (pdf_to_xlsx, 'xlsx'),
    'PDF vers PowerPoint (texte)': (pdf_to_pptx, 'pptx'),
    'Extraire le texte': (extract_text, 'txt'),
}

def run_conversion(app, target, *, select_source=None, select_destination=None, confirm_replace=None):
    """Select inputs and execute conversion; cancellation never queues a job.

    Dialogs are injectable to test the exact user journey without Tk/display.
    """
    if target not in CONVERSIONS:
        raise ValueError('Conversion inconnue')
    if getattr(app, 'busy', False) or getattr(app, '_v272_busy', False):
        return False
    if select_source is None or select_destination is None or confirm_replace is None:
        from tkinter import filedialog, messagebox
        select_source = select_source or (lambda: filedialog.askopenfilename(parent=app, title='Sélectionner un PDF', filetypes=[('PDF', '*.pdf')]))
        select_destination = select_destination or (lambda source, ext: filedialog.asksaveasfilename(parent=app, title='Exporter en '+ext.upper(), initialfile=Path(source).stem+'.'+ext, defaultextension='.'+ext, filetypes=[(ext.upper(), '*.'+ext)]))
        confirm_replace = confirm_replace or (lambda dest: messagebox.askyesno('Remplacement', 'Remplacer le fichier existant ?', parent=app))
    operation, ext = CONVERSIONS[target]
    source = select_source()
    if not source:
        return False
    destination = select_destination(source, ext)
    if not destination:
        return False
    dest = Path(destination)
    if dest.suffix.lower() != '.'+ext:
        raise ValueError('Extension de sortie incompatible')
    if dest.exists() and not confirm_replace(dest):
        return False
    # V30.1 routes this operation to the transactional conversion controller.
    app._run_pdf(operation, source, destination)
    return True

def activate(app, target):
    if target in CONVERSIONS:
        return run_conversion(app, target)
    if getattr(app, 'busy', False) or getattr(app, '_v272_busy', False):
        return False
    if target not in ('merge_async', 'extract_async', 'compress_async'):
        raise ValueError('Action rapide inconnue')
    getattr(app, target)()
    return True

def connect(app):
    connect_previous(app)
    if getattr(app, '_v303_connected', False):
        return app
    app._v303_connected = True
    # Rebind quick action keyboard shortcuts to direct dialogs, not a combo box.
    import tkinter as tk
    if isinstance(app, tk.Tk):
        for _, target, shortcut in ACTIONS:
            if target in CONVERSIONS:
                key = '<' + shortcut.replace('Ctrl','Control').replace('Maj','Shift').replace('+','-') + '>'
                app.bind(key, lambda event, t=target: activate(app, t))
        menu = app.nametowidget(app.cget('menu'))
        direct = tk.Menu(menu, tearoff=False)
        for title, target, _ in ACTIONS:
            if target in CONVERSIONS:
                direct.add_command(label=title, command=lambda t=target: activate(app,t))
        menu.add_cascade(label='Convertir directement', menu=direct)
        app.configure(menu=menu)
    return app
