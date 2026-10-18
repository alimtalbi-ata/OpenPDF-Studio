"""V30.5: searchable, keyboard-accessible workspace. Author: Abdelhalim Talbi."""
from openpdf_workspace_v304 import available_actions, dispatch

def search_actions(query=''):
    """Case-insensitive accent-insensitive matching across category, label and shortcut."""
    import unicodedata
    def norm(s):
        return ''.join(c for c in unicodedata.normalize('NFKD', str(s)).casefold() if not unicodedata.combining(c))
    words = norm(query).split()
    return tuple(action for action in available_actions() if all(word in norm(' '.join(action)) for word in words))

def connect(app):
    from openpdf_workspace_v304 import connect as previous
    previous(app)
    if getattr(app, '_v305_connected', False):
        return app
    app._v305_connected = True
    import tkinter as tk
    from tkinter import ttk
    if not isinstance(app, tk.Tk):
        return app
    def open_search(event=None):
        existing=getattr(app, '_v305_search_window', None)
        try:
            if existing is not None and existing.winfo_exists():
                existing.lift(); existing.focus_set(); return 'break'
        except tk.TclError:
            pass
        dialog=tk.Toplevel(app)
        app._v305_search_window=dialog
        dialog.title('Rechercher une action — OpenPDF Studio')
        dialog.transient(app)
        dialog.minsize(500, 320)
        frame=ttk.Frame(dialog, padding=14)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame,text='Rechercher une fonction',font=('Segoe UI',13,'bold')).pack(anchor='w')
        query=tk.StringVar()
        entry=ttk.Entry(frame,textvariable=query)
        entry.pack(fill='x',pady=(8,10))
        results=ttk.Treeview(frame,columns=('group','shortcut'),show='tree headings',selectmode='browse')
        results.heading('#0',text='Action'); results.heading('group',text='Catégorie'); results.heading('shortcut',text='Raccourci')
        results.column('#0',width=240); results.column('group',width=150); results.column('shortcut',width=85)
        results.pack(fill='both',expand=True)
        actions=[]
        def refresh(*_):
            nonlocal actions
            actions=list(search_actions(query.get()))
            for item in results.get_children(): results.delete(item)
            for i,(group,label,target,shortcut) in enumerate(actions):
                results.insert('', 'end',iid=str(i),text=label,values=(group,shortcut))
            if actions: results.selection_set('0'); results.focus('0')
        def execute(event=None):
            selected=results.selection()
            if not selected: return 'break'
            target=actions[int(selected[0])][2]
            if dispatch(app,target): dialog.destroy()
            return 'break'
        query.trace_add('write',refresh)
        results.bind('<Double-1>',execute)
        results.bind('<Return>',execute)
        entry.bind('<Return>',execute)
        dialog.bind('<Escape>',lambda e:dialog.destroy())
        ttk.Button(frame,text='Exécuter l’action sélectionnée',command=execute).pack(anchor='e',pady=(10,0))
        refresh();entry.focus_set()
        return 'break'
    app.bind('<Control-k>',open_search)
    menu_name=app.cget('menu')
    menu=app.nametowidget(menu_name) if menu_name else tk.Menu(app)
    search_menu=tk.Menu(menu,tearoff=False)
    search_menu.add_command(label='Rechercher une action    Ctrl+K',command=open_search)
    menu.add_cascade(label='Recherche',menu=search_menu)
    app.configure(menu=menu)
    return app
