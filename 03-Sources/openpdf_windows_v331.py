"""V33.1 — integration du bilan dans la fin de tâche Tk (thread UI)."""
from pathlib import Path
from tkinter import messagebox
from openpdf_windows_v330 import OpenPDFStudio as Previous
from openpdf_task_state_v274 import Phase
from openpdf_quality_dashboard_v330 import build_summary, show_summary_dialog

COMPRESSION_OPERATIONS = frozenset({'compress_with_profile', 'compression_with_report', 'compress_with_receipt'})

class OpenPDFStudio(Previous):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._v331_compression = None
        self.title('OpenPDF Studio V33.1 — Abdelhalim Talbi')

    def _run_pdf(self, operation, *args):
        # Ne mémoriser que les traitements effectivement soumis.
        if self._task_state.busy:
            return super()._run_pdf(operation, *args)
        is_compression = getattr(operation, '__name__', '') in COMPRESSION_OPERATIONS
        self._v331_compression = (str(args[0]), str(args[1])) if is_compression and len(args) >= 2 else None
        try:
            return super()._run_pdf(operation, *args)
        except Exception:
            self._v331_compression = None
            raise

    def _poll_v274(self):
        # Reprend le cycle existant, sans toucher au thread worker.
        handle = self._v273_handle
        if handle is None:
            return
        self._v273_progress.configure(value=round(handle.progress * 100))
        if not handle.future.done():
            self.after(100, self._poll_v274)
            return
        result = handle.future.result()
        phase = self._task_state.finish(result)
        self._v273_handle = None
        self._v273_cancel.configure(state='disabled')
        self._v273_label.configure(text={Phase.SUCCEEDED:'Terminé', Phase.FAILED:'Échec', Phase.CANCELLED:'Annulé'}[phase])
        compression = self._v331_compression
        self._v331_compression = None
        if phase == Phase.FAILED:
            messagebox.showerror('Erreur PDF', str(result.error), parent=self)
        elif phase == Phase.SUCCEEDED:
            if compression and Path(compression[1]).is_file():
                try:
                    show_summary_dialog(self, build_summary(*compression))
                except (OSError, ValueError) as exc:
                    messagebox.showwarning('Bilan indisponible', str(exc), parent=self)
                    messagebox.showinfo('Terminé', f'Résultat : {result.value}', parent=self)
            else:
                messagebox.showinfo('Terminé', f'Résultat : {result.value}', parent=self)

if __name__ == '__main__':
    OpenPDFStudio().mainloop()
