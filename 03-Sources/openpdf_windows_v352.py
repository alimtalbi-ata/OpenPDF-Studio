"""OpenPDF Studio V35.2 — stable UI entrypoint. Abdelhalim Talbi."""
from openpdf_windows_v351 import OpenPDFStudio as Base
class OpenPDFStudio(Base):
    def __init__(self):
        super().__init__()
        self.title('OpenPDF Studio V35.2 — Abdelhalim Talbi')
if __name__=='__main__':
    OpenPDFStudio().mainloop()
