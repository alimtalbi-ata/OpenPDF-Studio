"""V27.5: centralized UI errors and diagnostics. Author: Abdelhalim Talbi."""
from tkinter import messagebox
from openpdf_windows_v274 import OpenPDFStudio as PreviousStudio
from openpdf_task_state_v274 import Phase
from openpdf_diagnostics_v275 import configure_logging, log_exception

class OpenPDFStudio(PreviousStudio):
    def __init__(self):
        self._diagnostics = configure_logging()
        super().__init__()
        self.title('OpenPDF Studio V27.5 — Abdelhalim Talbi')
        self._diagnostics.info('Application started')

    def report_callback_exception(self, exc, value, tb):
        log_exception(self._diagnostics, 'UI callback', value)
        messagebox.showerror('Erreur', 'Une erreur est survenue. Consultez le journal de diagnostic.')

    def _poll_v274(self):
        handle = self._v273_handle
        if handle is None:
            return
        self._v273_progress.configure(value=round(handle.progress * 100))
        if not handle.future.done():
            self.after(100, self._poll_v274)
            return
        try:
            result = handle.future.result()
            phase = self._task_state.finish(result)
        except Exception as error:
            log_exception(self._diagnostics, 'Task completion', error)
            self._v273_handle = None
            self._v273_cancel.configure(state='disabled')
            self._v273_label.configure(text='Échec')
            messagebox.showerror('Erreur PDF', 'Échec du traitement. Consultez le journal.')
            return
        self._v273_handle = None
        self._v273_cancel.configure(state='disabled')
        self._v273_label.configure(text={Phase.SUCCEEDED:'Terminé', Phase.FAILED:'Échec', Phase.CANCELLED:'Annulé'}[phase])
        if phase == Phase.FAILED:
            log_exception(self._diagnostics, 'PDF task', result.error)
            messagebox.showerror('Erreur PDF', 'Le traitement a échoué. Consultez le journal.')
        elif phase == Phase.SUCCEEDED:
            messagebox.showinfo('Terminé', f'Fichier créé : {result.value}')

if __name__ == '__main__':
    OpenPDFStudio().mainloop()
