"""V31.2 — discoverable common actions, responsive layout and safe status hints.
Author: Abdelhalim Talbi.
"""
from openpdf_essentials_v311 import ESSENTIALS, launch, connect as connect_previous

SHORTCUTS = (("<Control-Shift-m>", "merge_async"),
             ("<Control-Shift-c>", "compress_async"),
             ("<Control-Shift-d>", "extract_async"),
             ("<Control-Shift-w>", "PDF vers Word (texte)"))

def help_message(action):
    for title, description, target in ESSENTIALS:
        if action == target:
            return f"{title} — {description}"
    raise ValueError(f"Action inconnue : {action}")

def safe_launch(app, action):
    if action not in {entry[2] for entry in ESSENTIALS}:
        return False
    return launch(app, action)

def connect(app):
    connect_previous(app)
    if getattr(app, '_v312_connected', False):
        return app
    app._v312_connected = True
    import tkinter as tk
    from tkinter import ttk
    if not isinstance(app, tk.Tk):
        return app
    panel = getattr(app, '_v311_essentials', None)
    if panel is None:
        return app
    # The legacy strip is already replaced by V31.1. Rebuild its content into
    # two columns: buttons stay legible on narrower Windows displays.
    for child in panel.winfo_children():
        child.destroy()
    panel.configure(text='Actions courantes — choisir une opération')
    for index, (title, description, target) in enumerate(ESSENTIALS):
        label = f"{title}  ›"
        button = ttk.Button(panel, text=label, command=lambda t=target: safe_launch(app,t))
        button.grid(row=index//2, column=index%2, sticky='ew', padx=5, pady=4)
        # Hints are restored only if unchanged, so they do not overwrite a
        # processing status emitted while the mouse is over the button.
        def enter(event, message=description):
            status=getattr(app,'status',None)
            if status is not None:
                previous=status.get()
                status.set(message)
                event.widget._hint=(message,previous)
        def leave(event):
            status=getattr(app,'status',None)
            hint=getattr(event.widget,'_hint',None)
            if status is not None and hint and status.get()==hint[0]:
                status.set(hint[1])
        button.bind('<Enter>',enter)
        button.bind('<Leave>',leave)
    panel.columnconfigure(0,weight=1)
    panel.columnconfigure(1,weight=1)
    for sequence, action in SHORTCUTS:
        app.bind(sequence, lambda event, a=action: safe_launch(app,a))
    return app
