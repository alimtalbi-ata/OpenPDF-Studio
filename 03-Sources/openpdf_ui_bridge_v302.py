"""V30.2: unified discoverable quick actions for PDF and editable exports.
Author: Abdelhalim Talbi. Tk-independent action specification and Tk adapter.
"""
from openpdf_ui_bridge_v301 import connect as connect_previous

ACTIONS = (
    ('Fusionner des PDF', 'merge_async', 'Ctrl+Maj+M'),
    ('Découper / extraire des pages', 'extract_async', 'Ctrl+Maj+D'),
    ('Compresser / optimiser', 'compress_async', 'Ctrl+Maj+C'),
    ('PDF vers Word', 'PDF vers Word (texte)', 'Ctrl+Alt+W'),
    ('PDF vers Excel', 'PDF vers Excel (lignes)', 'Ctrl+Alt+E'),
    ('PDF vers PowerPoint', 'PDF vers PowerPoint (texte)', 'Ctrl+Alt+P'),
    ('Extraire le texte', 'Extraire le texte', 'Ctrl+Alt+T'),
)

def activate(app, target):
    """Dispatch an action to the existing GUI without bypassing its validation."""
    if getattr(app, 'busy', False) or getattr(app, '_v272_busy', False):
        return False
    if target in ('merge_async', 'extract_async', 'compress_async'):
        getattr(app, target)()
    else:
        app.operation.set(target)
        app._refresh()
        if hasattr(app, 'combo'):
            app.combo.focus_set()
    return True

def connect(app):
    connect_previous(app)
    if getattr(app, '_v302_connected', False):
        return app
    app._v302_connected = True
    import tkinter as tk
    from tkinter import ttk
    if not isinstance(app, tk.Tk):
        return app
    menu_value = app.cget('menu')
    menu = app.nametowidget(menu_value) if menu_value else tk.Menu(app)
    actions_menu = tk.Menu(menu, tearoff=False)
    for label, target, shortcut in ACTIONS:
        actions_menu.add_command(label=f'{label}    {shortcut}', command=lambda t=target: activate(app,t))
    menu.add_cascade(label='Actions rapides', menu=actions_menu)
    app.configure(menu=menu)
    # A compact, persistent toolbar makes the most-used actions visible.
    toolbar = ttk.Frame(app, padding=(12, 5))
    for label, target, _ in ACTIONS:
        if target in ('merge_async','extract_async','compress_async'):
            ttk.Button(toolbar, text=label, command=lambda t=target: activate(app,t)).pack(side='left',padx=3)
    toolbar.pack(side='top', fill='x', before=app.main_panes if hasattr(app,'main_panes') else None)
    for _, target, shortcut in ACTIONS:
        key = '<' + shortcut.replace('Ctrl','Control').replace('Maj','Shift').replace('Alt','Alt').replace('+','-') + '>'
        app.bind(key, lambda event, t=target: activate(app,t))
    return app
