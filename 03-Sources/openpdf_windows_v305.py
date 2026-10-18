"""OpenPDF Studio V30.5 — Abdelhalim Talbi."""
from openpdf_windows_v293 import OpenPDFStudio as ApplicationCore
from openpdf_workspace_v305 import connect
class OpenPDFStudio(ApplicationCore):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.title('OpenPDF Studio V30.5 — Abdelhalim Talbi')
        connect(self)
def create_app(): return OpenPDFStudio()
if __name__=='__main__': create_app().mainloop()
