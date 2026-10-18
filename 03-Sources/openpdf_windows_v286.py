"""Windows V28.6 entrypoint. Author: Abdelhalim Talbi."""
from openpdf_windows_v285 import OpenPDFStudio as PreviousStudio
class OpenPDFStudio(PreviousStudio):
    def __init__(self):
        super().__init__()
        self.title("OpenPDF Studio V28.6 — Abdelhalim Talbi")
if __name__ == "__main__":
    OpenPDFStudio().mainloop()
