"""V27.4: single visible task status, controlled shutdown. Abdelhalim Talbi."""
from tkinter import messagebox
from openpdf_windows_v273 import OpenPDFStudio as PreviousStudio
from openpdf_task_state_v274 import TaskState, Phase
from openpdf_engine_v273 import merge_pdfs, extract_pages, compress_pdf

class OpenPDFStudio(PreviousStudio):
    def __init__(self):
        super().__init__()
        self.title('OpenPDF Studio V27.4 — Abdelhalim Talbi')
        self._task_state=TaskState()
        # Hide obsolete V27.2 activity bar; V27.3 status is the single source of truth.
        self._v272_bar.pack_forget()
        self.protocol('WM_DELETE_WINDOW',self._close_v274)

    def _run_pdf(self, operation, *args):
        if self._task_state.busy:
            messagebox.showinfo('Traitement','Un traitement est déjà en cours.');return
        operation={'merge_pdfs':merge_pdfs,'extract_pages':extract_pages,'compress_pdf':compress_pdf}.get(operation.__name__,operation)
        handle=self._v273_runner.submit(operation,*args)
        self._task_state.start(handle)
        self._v273_handle=handle
        self._v273_cancel.configure(state='normal')
        self._v273_progress.configure(value=0)
        self._v273_label.configure(text='Traitement en cours…')
        self.after(100,self._poll_v274)

    def _cancel_v273(self):
        if self._task_state.cancel():
            self._v273_label.configure(text='Annulation demandée…')
            self._v273_cancel.configure(state='disabled')

    def _poll_v274(self):
        handle=self._v273_handle
        if handle is None:return
        self._v273_progress.configure(value=round(handle.progress*100))
        if not handle.future.done():
            self.after(100,self._poll_v274);return
        result=handle.future.result()
        phase=self._task_state.finish(result)
        self._v273_handle=None
        self._v273_cancel.configure(state='disabled')
        self._v273_label.configure(text={Phase.SUCCEEDED:'Terminé',Phase.FAILED:'Échec',Phase.CANCELLED:'Annulé'}[phase])
        if phase==Phase.FAILED:messagebox.showerror('Erreur PDF',str(result.error))
        elif phase==Phase.SUCCEEDED:messagebox.showinfo('Terminé',f'Fichier créé : {result.value}')

    def _close_v274(self):
        if self._task_state.busy:
            messagebox.showwarning('Traitement actif','Annulez le traitement et attendez sa fin avant de quitter.');return
        self._v273_runner.shutdown()
        # Runner inherited from V27.1 remains available for compatibility.
        if hasattr(self,'task_runner'):
            try:self.task_runner.shutdown()
            except Exception:pass
        self.destroy()

if __name__=='__main__':OpenPDFStudio().mainloop()
