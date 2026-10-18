"""OpenPDF Studio V31.8 — packaging/documentation release. Author Abdelhalim Talbi."""
from openpdf_windows_v316 import OpenPDFStudio as Previous
class OpenPDFStudio(Previous):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.title('OpenPDF Studio V31.8 — Abdelhalim Talbi')
def create_app(): return OpenPDFStudio()
if __name__=='__main__': create_app().mainloop()
