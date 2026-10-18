"""V33.5 — présentation locale, sans mutation du module historique."""
from tkinter import messagebox
from openpdf_windows_v334 import OpenPDFStudio as Previous
from openpdf_task_presenter_v334 import completion_view
from openpdf_quality_dashboard_v332 import validate_output, show_summary_dialog

class OpenPDFStudio(Previous):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("OpenPDF Studio V33.5 — Abdelhalim Talbi")

    def _poll_v274(self):
        handle = self._v273_handle
        if handle is None:
            return
        if not handle.future.done():
            self._v273_progress.configure(value=max(0, min(100, round(handle.progress * 100))))
            self.after(100, self._poll_v274)
            return
        try:
            result = handle.future.result()
            phase = self._task_state.finish(result)
            view = completion_view(phase, result, self._v331_compression)
        except Exception as exc:
            messagebox.showerror("Erreur de traitement", str(exc), parent=self)
            self._v273_label.configure(text="Erreur interne")
            return
        finally:
            self._v273_handle = None
            self._v331_compression = None
            self._v273_cancel.configure(state="disabled")
        labels = {"cancelled": "Annulé", "error": "Échec", "warning": "Non confirmé", "success": "Terminé", "compression": "Terminé"}
        self._v273_label.configure(text=labels.get(view.kind, "Non confirmé"))
        if view.kind == "cancelled":
            return
        if view.kind == "error":
            messagebox.showerror("Erreur PDF", view.message, parent=self)
        elif view.kind == "warning":
            messagebox.showwarning("Résultat non confirmé", view.message, parent=self)
        elif view.kind == "success":
            messagebox.showinfo("Terminé", "Résultat : " + view.message, parent=self)
        elif view.kind == "compression":
            try:
                summary = validate_output(*view.compression)
                show_summary_dialog(self, summary)
            except (OSError, ValueError) as exc:
                messagebox.showwarning("Bilan non vérifiable", str(exc), parent=self)

if __name__ == "__main__":
    OpenPDFStudio().mainloop()
