"""V33.6: UI result dispatcher, stale polling and race guards."""
from tkinter import messagebox
from openpdf_windows_v335 import OpenPDFStudio as Previous
from openpdf_task_presenter_v334 import completion_view
from openpdf_quality_dashboard_v332 import validate_output, show_summary_dialog

class OpenPDFStudio(Previous):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.title("OpenPDF Studio V33.6 — Abdelhalim Talbi")

    def _poll_v274(self):
        handle = self._v273_handle
        if handle is None:
            return
        try:
            progress = max(0,min(100,round(handle.progress*100)))
            if handle is not self._v273_handle:
                return
            self._v273_progress.configure(value=progress)
            if not handle.future.done():
                self.after(100,self._poll_v274)
                return
            # Snapshot task metadata before releasing the completed handle.
            compression = self._v331_compression
            result = handle.future.result()
            phase = self._task_state.finish(result)
            view = completion_view(phase,result,compression)
        except Exception as exc:
            if handle is self._v273_handle:
                self._v273_label.configure(text="Erreur interne")
                messagebox.showerror("Erreur de traitement",str(exc),parent=self)
            return
        finally:
            owns_completed = handle.future.done() and handle is self._v273_handle
            if owns_completed:
                self._v273_handle = None
                self._v331_compression = None
                self._v273_cancel.configure(state="disabled")
        if not owns_completed:
            return  # Another task replaced this one: no stale result dialog.
        labels={"cancelled":"Annulé","error":"Échec","warning":"Non confirmé","success":"Terminé","compression":"Terminé"}
        self._v273_label.configure(text=labels.get(view.kind,"Non confirmé"))
        if view.kind == "cancelled":return
        if view.kind == "error":messagebox.showerror("Erreur PDF",view.message,parent=self)
        elif view.kind == "warning":messagebox.showwarning("Résultat non confirmé",view.message,parent=self)
        elif view.kind == "success":messagebox.showinfo("Terminé","Résultat : "+view.message,parent=self)
        elif view.kind == "compression":
            try:show_summary_dialog(self,validate_output(*view.compression))
            except (OSError,ValueError) as exc:messagebox.showwarning("Bilan non vérifiable",str(exc),parent=self)

if __name__ == "__main__":OpenPDFStudio().mainloop()
