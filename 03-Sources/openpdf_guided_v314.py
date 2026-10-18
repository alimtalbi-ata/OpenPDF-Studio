"""V31.4: one discoverable, safe entry point for everyday PDF tasks.
Author: Abdelhalim Talbi.
"""
from openpdf_guided_v313 import connect as connect_previous, guided_word
from openpdf_essentials_v311 import ESSENTIALS

COMMON_ACTIONS = {"merge_async", "compress_async", "extract_async"}

def task_description(action):
    descriptions = {
        "merge_async": "1. Sélectionnez plusieurs PDF. 2. Choisissez le fichier fusionné. 3. Lancez.",
        "compress_async": "1. Sélectionnez un PDF. 2. Choisissez le fichier allégé. 3. Lancez.",
        "extract_async": "1. Sélectionnez un PDF. 2. Indiquez les pages. 3. Enregistrez.",
        "PDF vers Word (texte)": "1. Sélectionnez un PDF. 2. Choisissez le document Word. 3. Convertissez.",
    }
    if action not in descriptions:
        raise ValueError("Action inconnue")
    return descriptions[action]

def launch_guided(app, action):
    """Reuse existing async handlers; never perform PDF work on the UI thread."""
    if action not in COMMON_ACTIONS and action != "PDF vers Word (texte)":
        return False
    if getattr(app, "busy", False) or getattr(app, "_v272_busy", False):
        return False
    if action == "PDF vers Word (texte)":
        return guided_word(app)
    handler = getattr(app, action, None)
    if not callable(handler):
        return False
    handler()
    return True

def connect(app):
    connect_previous(app)
    if getattr(app, "_v314_connected", False):
        return app
    app._v314_connected = True
    import tkinter as tk
    from tkinter import ttk
    if not isinstance(app, tk.Tk):
        return app
    panel = getattr(app, "_v311_essentials", None)
    if panel is None:
        return app
    panel.configure(text="Que souhaitez-vous faire avec vos PDF ?")
    for child in panel.winfo_children():
        child.destroy()
    for index, (title, _, action) in enumerate(ESSENTIALS):
        cell = ttk.Frame(panel, padding=(6, 5))
        cell.grid(row=index//2, column=index%2, sticky="nsew")
        ttk.Button(cell, text=title, command=lambda a=action: launch_guided(app,a)).pack(fill="x")
        ttk.Label(cell, text=task_description(action), wraplength=265, justify="left").pack(fill="x", pady=(5,0))
        cell.columnconfigure(0, weight=1)
    panel.columnconfigure(0,weight=1)
    panel.columnconfigure(1,weight=1)
    for sequence, action in (("<Control-Shift-m>","merge_async"), ("<Control-Shift-c>","compress_async"), ("<Control-Shift-d>","extract_async"), ("<Control-Shift-w>","PDF vers Word (texte)")):
        app.bind(sequence, lambda event, a=action: launch_guided(app,a))
    return app
