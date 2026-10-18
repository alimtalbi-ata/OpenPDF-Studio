"""V33.7: reject stale compression outputs and clean up failed polling."""
from tkinter import messagebox
from openpdf_windows_v336 import OpenPDFStudio as Previous
from openpdf_output_receipt_v337 import fingerprint, compression_publication
from openpdf_task_presenter_v334 import completion_view
from openpdf_quality_dashboard_v332 import validate_output, show_summary_dialog

class OpenPDFStudio(Previous):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self._v337_before = None
        self.title('OpenPDF Studio V33.7 — Abdelhalim Talbi')

    def _run_pdf(self, operation, *args):
        if self._task_state.busy:
            return super()._run_pdf(operation,*args)
        is_compression = getattr(operation,'__name__','') in {'compress_with_profile','compression_with_report','compress_with_receipt'}
        self._v337_before = fingerprint(args[1]) if is_compression and len(args)>=2 else None
        return super()._run_pdf(operation,*args)

    def _poll_v274(self):
        handle = self._v273_handle
        if handle is None: return
        if handle is not self._v273_handle: return
        try:
            self._v273_progress.configure(value=max(0,min(100,round(handle.progress*100))))
            if not handle.future.done():
                self.after(100,self._poll_v274)
                return
            compression = self._v331_compression
            before = self._v337_before
            result = handle.future.result()
            phase = self._task_state.finish(result)
            view = completion_view(phase,result,compression)
            if view.kind == 'compression':
                published, reason = compression_publication(before,compression[1],getattr(result,'value',None))
                if not published:
                    from openpdf_task_presenter_v334 import CompletionView
                    view = CompletionView('warning',reason)
        except Exception as exc:
            from openpdf_task_presenter_v334 import CompletionView
            view = CompletionView('error','Erreur interne de récupération : '+str(exc))
            try: self._task_state.finish(None)
            except Exception: pass
        finally:
            if handle.future.done() and handle is self._v273_handle:
                self._v273_handle = None
                self._v331_compression = None
                self._v337_before = None
                self._v273_cancel.configure(state='disabled')
        if handle is self._v273_handle: return
        self._v273_label.configure(text={'cancelled':'Annulé','error':'Échec','warning':'Non confirmé','success':'Terminé','compression':'Terminé'}.get(view.kind,'Non confirmé'))
        if view.kind == 'cancelled': return
        if view.kind == 'error': messagebox.showerror('Erreur PDF',view.message,parent=self)
        elif view.kind == 'warning': messagebox.showwarning('Résultat non confirmé',view.message,parent=self)
        elif view.kind == 'success': messagebox.showinfo('Terminé','Résultat : '+view.message,parent=self)
        elif view.kind == 'compression':
            try: show_summary_dialog(self,validate_output(*view.compression))
            except (OSError,ValueError) as exc: messagebox.showwarning('Bilan non vérifiable',str(exc),parent=self)

if __name__ == '__main__': OpenPDFStudio().mainloop()
