"""OpenPDF Studio V31.6 — documentation-integrated release."""
from openpdf_windows_v315 import OpenPDFStudio as Previous
class OpenPDFStudio(Previous):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.title('OpenPDF Studio V31.6 — Abdelhalim Talbi')
def create_app(): return OpenPDFStudio()
if __name__=='__main__': create_app().mainloop()
