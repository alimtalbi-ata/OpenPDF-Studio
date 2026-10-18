"""OpenPDF Studio V32.7 — Abdelhalim Talbi."""
from openpdf_windows_v326 import OpenPDFStudio as Previous
from openpdf_compression_v327 import connect
class OpenPDFStudio(Previous):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);connect(self)
        self.title('OpenPDF Studio V32.7 — Abdelhalim Talbi')
if __name__=='__main__':OpenPDFStudio().mainloop()
