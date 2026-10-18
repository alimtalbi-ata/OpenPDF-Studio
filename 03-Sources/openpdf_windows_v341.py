"""V34.1 entry point. Keep legacy UI until migration tests pass."""
from openpdf_windows_v340 import OpenPDFStudio as Previous
class OpenPDFStudio(Previous):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.title("OpenPDF Studio V34.1 — Abdelhalim Talbi")
if __name__ == "__main__":
    OpenPDFStudio().mainloop()
