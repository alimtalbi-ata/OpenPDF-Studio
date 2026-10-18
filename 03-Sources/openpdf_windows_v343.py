"""V34.3: orchestrator integrated for compression, without replacing legacy UI lifecycle."""
from openpdf_windows_v342 import OpenPDFStudio as Previous
from openpdf_orchestrator_v343 import JobOrchestrator, JobPhase
from openpdf_transaction_v338 import compress_with_receipt

class OpenPDFStudio(Previous):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self._v343_orchestrator=JobOrchestrator()
        self._v343_orchestrator.registry.register("pdf.compress",compress_with_receipt)
        self._v343_job_id=None
        self.title("OpenPDF Studio V34.3 — Abdelhalim Talbi")

    def _run_pdf(self,operation,*args):
        name=getattr(operation,"__name__","")
        is_compression=name in {"compress_with_profile","compress_with_receipt"}
        if not is_compression or len(args)<2:
            return super()._run_pdf(operation,*args)
        if getattr(self._task_state,"busy",False):
            return super()._run_pdf(operation,*args)
        decision,job=self._v343_orchestrator.submit("pdf.compress",str(args[0]),str(args[1]))
        if not decision.accepted:
            from tkinter import messagebox
            messagebox.showwarning("Compression non lancée",decision.reason,parent=self)
            return None
        self._v343_job_id=job.job_id
        try:
            outcome=super()._run_pdf(operation,*args)
            if getattr(self,"_v273_handle",None) is None:
                self._v343_orchestrator.abort_submission(job.job_id,"Aucune tâche démarrée")
                self._v343_job_id=None
            return outcome
        except BaseException as exc:
            self._v343_orchestrator.abort_submission(job.job_id,str(exc))
            self._v343_job_id=None
            raise

    def _poll_v274(self):
        handle=getattr(self,"_v273_handle",None)
        job_id=self._v343_job_id
        try:
            return super()._poll_v274()
        finally:
            if job_id and handle is not None and handle.future.done():
                phase=getattr(self._task_state,"phase",None)
                value=getattr(phase,"value",str(phase))
                mapping={"succeeded":JobPhase.SUCCEEDED,"failed":JobPhase.FAILED,"cancelled":JobPhase.CANCELLED}
                final=mapping.get(value,JobPhase.FAILED)
                self._v343_orchestrator.complete(job_id,final)
                if self._v343_job_id==job_id:self._v343_job_id=None

if __name__=="__main__":OpenPDFStudio().mainloop()
