"""V32.0 compression with verifiable size comparison. Author: Abdelhalim Talbi."""
from pathlib import Path
from openpdf_compression_v319 import validate_compression
from openpdf_engine_v272 import compress_pdf

def format_bytes(value):
    if value < 1024: return f"{value} octets"
    if value < 1024**2: return f"{value/1024:.1f} Kio"
    return f"{value/1024**2:.2f} Mio"

def compression_with_report(source, destination):
    source,destination=validate_compression(source,destination)
    before=Path(source).stat().st_size
    result=compress_pdf(source,destination)
    target=Path(destination)
    if not target.is_file(): raise RuntimeError("Le moteur n'a pas créé le PDF de sortie")
    after=target.stat().st_size
    delta=before-after
    percent=100*delta/before if before else 0
    verdict=(f"Gain : {format_bytes(delta)} ({percent:.1f} %)" if delta>0 else
             "Taille identique" if delta==0 else
             f"Augmentation : {format_bytes(-delta)} ({-percent:.1f} %) — conserver l'original si préférable")
    return f"{target}\nAvant : {format_bytes(before)}\nAprès : {format_bytes(after)}\n{verdict}"

def guided_compress(app, *, ask_source=None, ask_destination=None, confirm_replace=None, warn=None):
    from openpdf_compression_v319 import guided_compress as previous
    from unittest.mock import patch
    # Le moteur existant reçoit un adaptateur qui conserve son contrat asynchrone.
    original=app._run_pdf
    def dispatch(operation,source,destination):
        return original(compression_with_report,source,destination)
    try:
        app._run_pdf=dispatch
        return previous(app,ask_source=ask_source,ask_destination=ask_destination,confirm_replace=confirm_replace,warn=warn)
    finally:
        app._run_pdf=original

def connect(app):
    from openpdf_compression_v319 import connect as previous
    previous(app)
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
