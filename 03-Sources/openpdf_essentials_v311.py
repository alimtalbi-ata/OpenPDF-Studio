"""V31.1: prioritize common PDF workflows without changing the processing engine.
Author: Abdelhalim Talbi.
"""
from openpdf_ui_bridge_v302 import activate
from openpdf_ui_bridge_v310 import connect as connect_previous

ESSENTIALS = (
    ('Fusionner', 'Assembler plusieurs PDF en un document', 'merge_async'),
    ('Compresser', 'Réduire le poids d’un PDF', 'compress_async'),
    ('Découper', 'Extraire des pages d’un PDF', 'extract_async'),
    ('Vers Word', 'Convertir en document Word modifiable', 'PDF vers Word (texte)'),
)

def describe(target):
    for title, help_text, action in ESSENTIALS:
        if action == target:
            return help_text
    raise KeyError(target)

def launch(app, target):
    """Reuse existing UI validation and processing, never run PDF work in Tk callbacks."""
    if target not in {action for _, _, action in ESSENTIALS}:
        return False
    return activate(app, target)

def connect(app):
    connect_previous(app)
    if getattr(app, '_v311_connected', False):
        return app
    app._v311_connected = True
    import tkinter as tk
    from tkinter import ttk
    if not isinstance(app, tk.Tk):
        return app
    # Replace the older three-button strip with a single clear, four-task entry point.
    for widget in app.winfo_children():
        if isinstance(widget, ttk.Frame):
            labels = [child.cget('text') for child in widget.winfo_children() if isinstance(child, ttk.Button)]
            if len(labels) == 3 and all(any(keyword in label for label in labels) for keyword in ('Fusionner', 'Découper', 'Compresser')):
                widget.pack_forget()
                break
    panel = ttk.LabelFrame(app, text='Actions courantes', padding=(12, 7))
    for title, help_text, target in ESSENTIALS:
        button = ttk.Button(panel, text=title, command=lambda t=target: launch(app, t))
        button.pack(side='left', padx=(0, 8))
        # Tooltip via status bar, no extra popup or intrusive modal.
        button.bind('<Enter>', lambda event, s=help_text: app.status.set(s) if hasattr(app, 'status') else None)
        button.bind('<Leave>', lambda event: app.status.set('Prêt') if hasattr(app, 'status') else None)
    panel.pack(side='top', fill='x', before=app.main_panes if hasattr(app, 'main_panes') else None)
    app._v311_essentials = panel
    return app
