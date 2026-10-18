"""OpenPDF Studio V33.0 — Abdelhalim Talbi."""
from openpdf_windows_v329 import OpenPDFStudio as Previous
class OpenPDFStudio(Previous):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.title('OpenPDF Studio V33.0 — Abdelhalim Talbi')
if __name__=='__main__': OpenPDFStudio().mainloop()
