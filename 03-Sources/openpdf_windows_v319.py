"""OpenPDF Studio V31.9; author Abdelhalim Talbi."""
from openpdf_windows_v318 import OpenPDFStudio as Previous
from openpdf_compression_v319 import connect
class OpenPDFStudio(Previous):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        connect(self)
        self.title('OpenPDF Studio V31.9 — Abdelhalim Talbi')
def create_app():return OpenPDFStudio()
if __name__=='__main__':create_app().mainloop()
