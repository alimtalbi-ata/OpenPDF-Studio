"""V31.5: reorderable merge journey; same asynchronous PDF engine.
Author: Abdelhalim Talbi.
"""
from pathlib import Path
from openpdf_guided_v314 import connect as connect_previous, launch_guided as previous_launch
from openpdf_engine_v272 import merge_pdfs

def move_item(items, index, direction):
    """Pure reorder operation, preserving each file exactly once."""
    data = list(items)
    other = index + direction
    if direction not in (-1, 1) or index < 0 or other < 0 or other >= len(data):
        return data, index
    data[index], data[other] = data[other], data[index]
    return data, other

def validate_merge(paths, destination):
    files = [Path(p) for p in paths]
    if len(files) < 2 or len({str(p.resolve()).casefold() for p in files}) != len(files):
        raise ValueError('Choisissez au moins deux PDF distincts.')
    if any(not p.is_file() or p.suffix.lower() != '.pdf' for p in files):
        raise ValueError('Les sources doivent être des PDF existants.')
    target = Path(destination)
    if target.suffix.lower() != '.pdf' or target.parent.exists() is False:
        raise ValueError('Choisissez un PDF de sortie dans un dossier existant.')
    if str(target.resolve()).casefold() in {str(p.resolve()).casefold() for p in files}:
        raise ValueError('Le PDF de sortie ne peut pas remplacer une source.')
    return tuple(str(p) for p in files), str(target)

def guided_merge(app, *, ask_sources=None, ask_destination=None, confirm_replace=None, warn=None):
    if getattr(app,'busy',False) or getattr(app,'_v272_busy',False): return False
    from tkinter import filedialog, messagebox
    interactive = ask_sources is None
    if ask_sources is None:
        ask_sources=lambda: filedialog.askopenfilenames(parent=app,title='1/3 — Sélectionner les PDF',filetypes=[('PDF','*.pdf')])
    if ask_destination is None:
        ask_destination=lambda suggested: filedialog.asksaveasfilename(parent=app,title='3/3 — Enregistrer le PDF fusionné',initialfile=suggested,defaultextension='.pdf',filetypes=[('PDF','*.pdf')])
    if warn is None: warn=lambda msg: messagebox.showwarning('Fusionner',msg,parent=app)
    if confirm_replace is None: confirm_replace=lambda path: messagebox.askyesno('Remplacer ?',f'Le fichier existe déjà :\n{path}\nLe remplacer ?',parent=app)
    paths=list(ask_sources() or [])
    if not paths: return False
    # Reorder dialog is skipped for injected/headless selection callbacks.
    if len(paths)>1 and getattr(app,'tk',None) is not None and interactive:
        import tkinter as tk
        from tkinter import ttk
        dialog=tk.Toplevel(app); dialog.title('2/3 — Organiser les PDF');dialog.transient(app);dialog.grab_set()
        ttk.Label(dialog,text='Ordre de fusion : sélectionnez un fichier puis déplacez-le.').pack(padx=12,pady=8)
        listing=tk.Listbox(dialog,width=68,height=min(12,max(4,len(paths))))
        listing.pack(fill='both',expand=True,padx=12)
        def refresh(selected=0):
            listing.delete(0,'end')
            for p in paths: listing.insert('end',Path(p).name)
            listing.selection_set(selected);listing.activate(selected)
        refresh(); state={'ok':False}
        buttons=ttk.Frame(dialog);buttons.pack(padx=12,pady=12)
        def shift(direction):
            selected=listing.curselection()
            if not selected:return
            new,index=move_item(paths,selected[0],direction);paths[:]=new;refresh(index)
        ttk.Button(buttons,text='Monter ↑',command=lambda:shift(-1)).pack(side='left',padx=3)
        ttk.Button(buttons,text='Descendre ↓',command=lambda:shift(1)).pack(side='left',padx=3)
        def accept():state['ok']=True;dialog.destroy()
        ttk.Button(buttons,text='Continuer',command=accept).pack(side='left',padx=3)
        ttk.Button(buttons,text='Annuler',command=dialog.destroy).pack(side='left',padx=3)
        dialog.protocol('WM_DELETE_WINDOW',dialog.destroy)
        app.wait_window(dialog)
        if not state['ok']:return False
    suggested=Path(paths[0]).stem+'-fusion.pdf'
    destination=ask_destination(suggested)
    if not destination:return False
    try: sources,target=validate_merge(paths,destination)
    except ValueError as exc:warn(str(exc));return False
    if Path(target).exists() and not confirm_replace(target):return False
    app._run_pdf(merge_pdfs,sources,target)
    return True

def launch_guided(app,action):
    if action=='merge_async':return guided_merge(app)
    return previous_launch(app,action)

def connect(app):
    connect_previous(app)
    if getattr(app,'_v315_connected',False):return app
    app._v315_connected=True
    import tkinter as tk
    from tkinter import ttk
    if not isinstance(app,tk.Tk):return app
    panel=getattr(app,'_v311_essentials',None)
    if panel:
        for child in panel.winfo_children():
            for button in child.winfo_children():
                if isinstance(button,ttk.Button) and button.cget('text')=='Fusionner':
                    button.configure(command=lambda:guided_merge(app))
    app.bind('<Control-Shift-m>',lambda event:guided_merge(app))
    return app
