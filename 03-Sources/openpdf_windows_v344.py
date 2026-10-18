"""V34.4 UI bridge: stable compression service, legacy other operations."""
from openpdf_windows_v343 import OpenPDFStudio as Previous
from openpdf_compression_service_v344 import compress_with_receipt

class OpenPDFStudio(Previous):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self._v343_orchestrator.registry._operations['pdf.compress'] = compress_with_receipt
        self.title('OpenPDF Studio V34.4 — Abdelhalim Talbi')

    def _run_pdf(self,operation,*args):
        if getattr(operation,'__name__','') in {'compress_with_profile','compress_with_receipt'}:
            operation=compress_with_receipt
        return super()._run_pdf(operation,*args)

if __name__=='__main__':OpenPDFStudio().mainloop()
