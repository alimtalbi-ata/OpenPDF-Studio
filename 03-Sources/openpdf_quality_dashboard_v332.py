"""V33.2: bilan vérifiable, affichage cohérent, pas de faux succès."""
from pathlib import Path
from openpdf_quality_dashboard_v330 import format_summary

def validate_output(source, destination):
    src, dst = Path(source), Path(destination)
    if not src.is_file(): raise FileNotFoundError(f"Source absente : {src}")
    if not dst.is_file(): raise FileNotFoundError(f"Sortie absente : {dst}")
    if src.resolve() == dst.resolve(): raise ValueError("Source et destination identiques : bilan non fiable")
    if dst.stat().st_size == 0: raise ValueError("Sortie vide : compression non validée")
    from openpdf_quality_dashboard_v330 import build_summary
    return build_summary(src, dst)

def show_summary_dialog(app, data):
    import tkinter as tk
    from tkinter import ttk
    dialog = tk.Toplevel(app)
    dialog.title("Bilan de compression — V33.2")
    dialog.minsize(520, 320)
    dialog.geometry("650x380")
    dialog.transient(app)
    dialog.columnconfigure(0, weight=1); dialog.rowconfigure(0, weight=1)
    frame = ttk.Frame(dialog, padding=18); frame.grid(sticky="nsew")
    frame.columnconfigure(0, weight=1); frame.rowconfigure(1, weight=1)
    ttk.Label(frame, text="Compression terminée", font=("Segoe UI", 15, "bold")).grid(row=0,column=0,sticky="w",pady=(0,12))
    content = tk.Text(frame, wrap="word", height=10, relief="flat", font=("Segoe UI", 10))
    content.grid(row=1,column=0,sticky="nsew")
    content.insert("1.0", format_summary(data)); content.configure(state="disabled")
    bar=ttk.Frame(frame); bar.grid(row=2,column=0,sticky="ew",pady=(12,0))
    def copy():
        dialog.clipboard_clear(); dialog.clipboard_append(format_summary(data)); dialog.update_idletasks()
    ttk.Button(bar,text="Copier le bilan",command=copy).pack(side="left")
    ttk.Button(bar,text="Fermer",command=dialog.destroy).pack(side="right")
    dialog.bind("<Escape>",lambda _e:dialog.destroy())
    dialog.protocol("WM_DELETE_WINDOW",dialog.destroy)
    dialog.focus_set()
    return dialog
