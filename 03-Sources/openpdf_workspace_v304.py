"""One discoverable task picker, no new inheritance chain. Abdelhalim Talbi."""
from openpdf_ui_bridge_v302 import ACTIONS
from openpdf_ui_bridge_v303 import activate

GROUPS = (
    ('Organiser les PDF', ('merge_async', 'extract_async', 'compress_async')),
    ('Convertir et exporter', tuple(action for _, action, _ in ACTIONS if action not in ('merge_async','extract_async','compress_async'))),
)

def available_actions():
    """Stable, UI-independent catalog used to build the workspace."""
    return tuple((group, label, target, shortcut) for group, targets in GROUPS
                 for label, target, shortcut in ACTIONS if target in targets)

def dispatch(app, target):
    if target not in {a for _, a, _ in ACTIONS}:
        raise ValueError('Action inconnue')
    return activate(app, target)

def connect(app):
    from openpdf_ui_bridge_v303 import connect as previous
    previous(app)
    if getattr(app, '_v304_connected', False):
        return app
    app._v304_connected = True
    import tkinter as tk
    from tkinter import ttk
    if not isinstance(app, tk.Tk):
        return app
    def open_workspace(event=None):
        if getattr(app, '_v304_dialog', None) is not None:
            try:
                if app._v304_dialog.winfo_exists():
                    app._v304_dialog.lift()
                    app._v304_dialog.focus_set()
                    return
            except tk.TclError:
                pass
        dialog = tk.Toplevel(app)
        app._v304_dialog = dialog
        dialog.title('Espace de travail — OpenPDF Studio')
        dialog.transient(app)
        dialog.resizable(True, True)
        dialog.minsize(460, 330)
        container = ttk.Frame(dialog, padding=16)
        container.pack(fill='both', expand=True)
        ttk.Label(container, text='Que souhaitez-vous faire ?', font=('Segoe UI', 15, 'bold')).pack(anchor='w', pady=(0,12))
        for group, targets in GROUPS:
            frame = ttk.LabelFrame(container, text=group, padding=8)
            frame.pack(fill='x', pady=5)
            for label, target, shortcut in ACTIONS:
                if target not in targets:
                    continue
                def choose(t=target):
                    if dispatch(app,t):
                        dialog.destroy()
                ttk.Button(frame, text=label, command=choose).pack(side='top', fill='x', pady=2)
        ttk.Label(container, text='Raccourci : F6 pour ouvrir cet espace · Échap pour fermer').pack(anchor='w', pady=(10,0))
        dialog.bind('<Escape>', lambda event: dialog.destroy())
        dialog.focus_set()
    app.bind('<F6>', open_workspace)
    menu_name = app.cget('menu')
    menu = app.nametowidget(menu_name) if menu_name else tk.Menu(app)
    workspace = tk.Menu(menu, tearoff=False)
    workspace.add_command(label='Ouvrir l’espace de travail    F6', command=open_workspace)
    menu.add_cascade(label='Espace de travail', menu=workspace)
    app.configure(menu=menu)
    return app
