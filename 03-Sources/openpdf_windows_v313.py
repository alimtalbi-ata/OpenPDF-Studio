"""OpenPDF Studio V31.3 — Abdelhalim Talbi."""
from openpdf_windows_v312 import OpenPDFStudio as Previous
from openpdf_guided_v313 import connect
class OpenPDFStudio(Previous):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        connect(self)
        self.title('OpenPDF Studio V31.3 — Abdelhalim Talbi')
def create_app(): return OpenPDFStudio()
if __name__=='__main__': create_app().mainloop()
