"""Windows V28.5 entrypoint. Author: Abdelhalim Talbi."""
from openpdf_windows_v284 import OpenPDFStudio as PreviousStudio
class OpenPDFStudio(PreviousStudio):
    def __init__(self):
        super().__init__()
        self.title("OpenPDF Studio V28.5 — Abdelhalim Talbi")
if __name__ == "__main__":
    OpenPDFStudio().mainloop()
