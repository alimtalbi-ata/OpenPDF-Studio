"""OpenPDF Studio V35.4 — stable Windows entrypoint. Abdelhalim Talbi."""
from openpdf_windows_v352 import OpenPDFStudio as Base
class OpenPDFStudio(Base):
    def __init__(self):
        super().__init__()
        self.title('OpenPDF Studio V35.4 — Abdelhalim Talbi')
if __name__=='__main__':
    OpenPDFStudio().mainloop()
