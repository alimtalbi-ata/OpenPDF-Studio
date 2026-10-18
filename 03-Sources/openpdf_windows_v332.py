"""V33.2: sécurisation des transitions et bilan de sortie."""
from pathlib import Path
from tkinter import messagebox
from openpdf_windows_v331 import OpenPDFStudio as Previous
from openpdf_task_state_v274 import Phase
from openpdf_quality_dashboard_v332 import validate_output, show_summary_dialog

class OpenPDFStudio(Previous):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.title("OpenPDF Studio V33.2 — Abdelhalim Talbi")

    def _poll_v274(self):
        handle = self._v273_handle
        if handle is None: return
        try:
            self._v273_progress.configure(value=round(handle.progress*100))
            if not handle.future.done():
                self.after(100,self._poll_v274); return
            result=handle.future.result()
            phase=self._task_state.finish(result)
        except Exception as exc:
            self._v273_handle=None; self._v331_compression=None
            self._v273_cancel.configure(state="disabled")
            self._v273_label.configure(text="Erreur interne")
            messagebox.showerror("Erreur de traitement",str(exc),parent=self)
            return
        self._v273_handle=None
        self._v273_cancel.configure(state="disabled")
        self._v273_label.configure(text={Phase.SUCCEEDED:"Terminé",Phase.FAILED:"Échec",Phase.CANCELLED:"Annulé"}.get(phase,"Statut inconnu"))
        compression=self._v331_compression
        self._v331_compression=None
        if phase==Phase.CANCELLED: return
        if phase==Phase.FAILED:
            messagebox.showerror("Erreur PDF",str(result.error),parent=self); return
        if phase!=Phase.SUCCEEDED:
            messagebox.showwarning("Statut inattendu",str(phase),parent=self); return
        if compression:
            try:
                show_summary_dialog(self,validate_output(*compression))
            except (OSError,ValueError) as exc:
                messagebox.showwarning("Bilan non vérifiable",str(exc),parent=self)
            return
        messagebox.showinfo("Terminé",f"Résultat : {result.value}",parent=self)

if __name__=="__main__": OpenPDFStudio().mainloop()
