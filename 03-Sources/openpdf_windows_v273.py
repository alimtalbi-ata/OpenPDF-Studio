"""V27.3 async controls, real progress and cancel. Author: Abdelhalim Talbi."""
from tkinter import ttk, messagebox
from openpdf_windows_v272 import OpenPDFStudio as PreviousStudio
from openpdf_engine_v273 import merge_pdfs,extract_pages,compress_pdf
from openpdf_tasks_v273 import TaskRunner

class OpenPDFStudio(PreviousStudio):
    def __init__(self):
        super().__init__()
        self.title('OpenPDF Studio V27.3 — Abdelhalim Talbi')
        self._v273_runner=TaskRunner(workers=1)
        self._v273_handle=None
        self._v273_status=ttk.Frame(self)
        self._v273_status.pack(side='bottom',fill='x')
        self._v273_label=ttk.Label(self._v273_status,text='Prêt')
        self._v273_label.pack(side='left',padx=8)
        self._v273_progress=ttk.Progressbar(self._v273_status,maximum=100,mode='determinate',length=180)
        self._v273_progress.pack(side='left',padx=8)
        self._v273_cancel=ttk.Button(self._v273_status,text='Annuler',command=self._cancel_v273,state='disabled')
        self._v273_cancel.pack(side='left',padx=8)
        self.protocol('WM_DELETE_WINDOW',self._close_v273)

    def _cancel_v273(self):
        if self._v273_handle:
            self._v273_handle.cancel()
            self._v273_label.configure(text='Annulation demandée…')

    def _run_pdf(self,operation,*args):
        if self._v273_handle is not None:
            messagebox.showinfo('Traitement','Un traitement est déjà en cours.');return
        operation={
            'merge_pdfs':merge_pdfs,'extract_pages':extract_pages,'compress_pdf':compress_pdf
        }.get(operation.__name__,operation)
        handle=self._v273_runner.submit(operation,*args)
        self._v273_handle=handle
        self._v273_cancel.configure(state='normal')
        self._v273_progress.configure(value=0)
        self._v273_label.configure(text='Traitement en cours…')
        self.after(100,self._poll_v273)

    def _poll_v273(self):
        handle=self._v273_handle
        if handle is None:return
        self._v273_progress.configure(value=round(handle.progress*100))
        if not handle.future.done():
            self.after(100,self._poll_v273);return
        self._v273_handle=None
        self._v273_cancel.configure(state='disabled')
        result=handle.future.result()
        if result.error:
            self._v273_label.configure(text='Annulé' if handle.cancelled() else 'Échec')
            if not handle.cancelled():messagebox.showerror('Erreur PDF',str(result.error))
        else:
            self._v273_label.configure(text='Terminé')
            messagebox.showinfo('Terminé',f'Fichier créé : {result.value}')

    def _close_v273(self):
        if self._v273_handle is not None:
            if not messagebox.askyesno('Quitter','Un traitement est en cours. Demander son annulation et quitter ?'):return
            self._v273_handle.cancel()
        self._v273_runner.shutdown()
        self.destroy()

if __name__=='__main__':OpenPDFStudio().mainloop()
