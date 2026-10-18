"""OpenPDF Studio V31.5 — Abdelhalim Talbi."""
from openpdf_windows_v314 import OpenPDFStudio as Previous
from openpdf_guided_v315 import connect
class OpenPDFStudio(Previous):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        connect(self)
        self.title('OpenPDF Studio V31.5 — Abdelhalim Talbi')
def create_app(): return OpenPDFStudio()
if __name__=='__main__': create_app().mainloop()
