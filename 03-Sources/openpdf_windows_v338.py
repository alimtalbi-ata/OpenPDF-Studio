"""V33.8: explicit compression receipt integration."""
from tkinter import messagebox
from openpdf_windows_v337 import OpenPDFStudio as Previous
from openpdf_transaction_v338 import compress_with_receipt, verify_receipt
from openpdf_task_presenter_v334 import completion_view, CompletionView
from openpdf_quality_dashboard_v332 import validate_output, show_summary_dialog

class OpenPDFStudio(Previous):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.title('OpenPDF Studio V33.8 — Abdelhalim Talbi')

    def _run_pdf(self, operation, *args):
        if getattr(operation,'__name__','') == 'compress_with_profile':
            operation = compress_with_receipt
        return super()._run_pdf(operation,*args)

    def _poll_v274(self):
        handle = self._v273_handle
        if handle is None:return
        try:
            self._v273_progress.configure(value=max(0,min(100,round(handle.progress*100))))
            if not handle.future.done():
                self.after(100,self._poll_v274)
                return
            result = handle.future.result()
            phase = self._task_state.finish(result)
            compression = self._v331_compression
            view = completion_view(phase,result,None)
            if compression and view.kind == 'success':
                valid,reason = verify_receipt(getattr(result,'value',None),compression[1])
                view = CompletionView('compression',compression=compression) if valid else CompletionView('warning',reason)
        except Exception as exc:
            view = CompletionView('error','Erreur de récupération : '+str(exc))
            try:self._task_state.finish(None)
            except Exception:pass
        finally:
            if handle.future.done() and handle is self._v273_handle:
                self._v273_handle = None
                self._v331_compression = None
                self._v337_before = None
                self._v273_cancel.configure(state='disabled')
        if handle is self._v273_handle:return
        self._v273_label.configure(text={'cancelled':'Annulé','error':'Échec','warning':'Non confirmé','success':'Terminé','compression':'Terminé'}.get(view.kind,'Non confirmé'))
        if view.kind == 'cancelled':return
        if view.kind == 'error':messagebox.showerror('Erreur PDF',view.message,parent=self)
        elif view.kind == 'warning':messagebox.showwarning('Résultat non confirmé',view.message,parent=self)
        elif view.kind == 'success':messagebox.showinfo('Terminé','Résultat : '+view.message,parent=self)
        elif view.kind == 'compression':
            try:show_summary_dialog(self,validate_output(*view.compression))
            except (OSError,ValueError) as exc:messagebox.showwarning('Bilan non vérifiable',str(exc),parent=self)

if __name__=='__main__':OpenPDFStudio().mainloop()
