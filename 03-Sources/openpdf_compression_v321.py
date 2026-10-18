"""V32.1 : profil standard ou conservation du plus petit PDF. Abdelhalim Talbi."""
from pathlib import Path
import os,tempfile
from openpdf_compression_v319 import validate_compression
from openpdf_engine_v272 import compress_pdf
from openpdf_compression_v320 import format_bytes

PROFILES = {"standard": "Optimisation sans perte", "smaller_only": "Conserver uniquement si plus petit"}

def compress_with_profile(source, destination, profile="smaller_only"):
    if profile not in PROFILES: raise ValueError("Profil inconnu")
    source,destination=validate_compression(source,destination)
    before=Path(source).stat().st_size
    fd,tmp=tempfile.mkstemp(prefix=".openpdf-",suffix=".pdf",dir=str(Path(destination).parent))
    os.close(fd)
    try:
        compress_pdf(source,tmp)
        after=Path(tmp).stat().st_size
        if profile=="smaller_only" and after>=before:
            return f"Aucun gain : original {format_bytes(before)}, candidat {format_bytes(after)}. Aucun fichier de sortie modifié."
        os.replace(tmp,destination)
        change=(before-after)*100/before if before else 0
        return f"{destination}\nAvant : {format_bytes(before)}\nAprès : {format_bytes(after)}\nGain : {change:.1f} %"
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def guided_compress(app, *, ask_source=None, ask_destination=None, choose_profile=None, confirm_replace=None, warn=None):
    if getattr(app,'busy',False) or getattr(app,'_v272_busy',False):return False
    from tkinter import filedialog,messagebox
    ask_source=ask_source or (lambda:filedialog.askopenfilename(parent=app,title='1/3 — PDF à optimiser',filetypes=[('PDF','*.pdf')]))
    ask_destination=ask_destination or (lambda name:filedialog.asksaveasfilename(parent=app,title='2/3 — PDF de sortie',initialfile=name,defaultextension='.pdf',filetypes=[('PDF','*.pdf')]))
    choose_profile=choose_profile or (lambda: 'smaller_only' if messagebox.askyesno('3/3 — Profil','Conserver uniquement si le PDF est plus petit ?\nOui : aucune sortie si le gain est nul.\nNon : enregistrer le résultat même si plus volumineux.',parent=app) else 'standard')
    warn=warn or (lambda msg:messagebox.showwarning('Optimiser un PDF',msg,parent=app))
    confirm_replace=confirm_replace or (lambda path:messagebox.askyesno('Remplacer ?',f'Le fichier existe :\n{path}\nLe remplacer si le profil produit un résultat ?',parent=app))
    source=ask_source()
    if not source:return False
    destination=ask_destination(Path(source).stem+'-optimise.pdf')
    if not destination:return False
    try:source,destination=validate_compression(source,destination)
    except ValueError as exc:warn(str(exc));return False
    profile=choose_profile()
    if profile is None:return False
    if profile not in PROFILES:warn('Profil inconnu');return False
    if Path(destination).exists() and not confirm_replace(destination):return False
    app._run_pdf(compress_with_profile,source,destination,profile)
    return True

def connect(app):
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
