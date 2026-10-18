"""OpenPDF Studio V28.2 Windows entrypoint. Author: Abdelhalim Talbi."""
from openpdf_windows_v281 import OpenPDFStudio as PreviousStudio
class OpenPDFStudio(PreviousStudio):
    def __init__(self):
        super().__init__()
        self.title('OpenPDF Studio V28.2 — Abdelhalim Talbi')
if __name__=='__main__': OpenPDFStudio().mainloop()
