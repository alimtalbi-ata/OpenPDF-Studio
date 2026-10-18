"""V34.6: expose independent Office conversion audit without changing legacy conversion behavior."""
from openpdf_windows_v345 import OpenPDFStudio as Previous
from openpdf_conversion_audit_v346 import audit_conversion
class OpenPDFStudio(Previous):
    conversion_audit=staticmethod(audit_conversion)
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.title('OpenPDF Studio V34.6 — Abdelhalim Talbi')
if __name__=='__main__':OpenPDFStudio().mainloop()
