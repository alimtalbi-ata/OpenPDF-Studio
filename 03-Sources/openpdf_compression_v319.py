"""V31.9 guided compression; structural lossless optimization, no guaranteed savings."""
from pathlib import Path
from openpdf_engine_v272 import compress_pdf

def validate_compression(source, destination):
    src=Path(source); target=Path(destination)
    if not src.is_file() or src.suffix.lower()!='.pdf':
        raise ValueError('Sélectionnez un fichier PDF existant.')
    if target.suffix.lower()!='.pdf' or not target.parent.is_dir():
        raise ValueError('La destination doit être un PDF dans un dossier existant.')
    if src.resolve()==target.resolve() or str(src.resolve()).casefold()==str(target.resolve()).casefold():
        raise ValueError('Le PDF original ne peut pas être écrasé.')
    return str(src),str(target)

def size_report(source,destination):
    a=Path(source).stat().st_size;b=Path(destination).stat().st_size
    return {'before_bytes':a,'after_bytes':b,'saved_bytes':a-b,'saved_percent':round((a-b)*100/a,2) if a else 0,'smaller':b<a}

def guided_compress(app, *, ask_source=None, ask_destination=None, confirm_replace=None, warn=None):
    if getattr(app,'busy',False) or getattr(app,'_v272_busy',False):return False
    from tkinter import filedialog,messagebox
    ask_source=ask_source or (lambda:filedialog.askopenfilename(parent=app,title='1/2 — PDF à optimiser',filetypes=[('PDF','*.pdf')]))
    ask_destination=ask_destination or (lambda name:filedialog.asksaveasfilename(parent=app,title='2/2 — Enregistrer le PDF optimisé',initialfile=name,defaultextension='.pdf',filetypes=[('PDF','*.pdf')]))
    warn=warn or (lambda msg:messagebox.showwarning('Optimiser un PDF',msg,parent=app))
    confirm_replace=confirm_replace or (lambda path:messagebox.askyesno('Remplacer ?',f'Le fichier existe :\n{path}\nLe remplacer ?',parent=app))
    source=ask_source()
    if not source:return False
    destination=ask_destination(Path(source).stem+'-optimise.pdf')
    if not destination:return False
    try:source,destination=validate_compression(source,destination)
    except ValueError as exc:warn(str(exc));return False
    if Path(destination).exists() and not confirm_replace(destination):return False
    app._run_pdf(compress_pdf,source,destination)
    return True

def connect(app):
    if getattr(app,'_v319_connected',False):return app
    app._v319_connected=True
    import tkinter as tk
    from tkinter import ttk
    if not isinstance(app,tk.Tk):return app
    panel=getattr(app,'_v311_essentials',None)
    if panel:
        for cell in panel.winfo_children():
            for widget in cell.winfo_children():
                if isinstance(widget,ttk.Button) and widget.cget('text') in ('Compresser','Optimiser'):
                    widget.configure(command=lambda:guided_compress(app))
    app.bind('<Control-Shift-c>',lambda event:guided_compress(app))
    return app
