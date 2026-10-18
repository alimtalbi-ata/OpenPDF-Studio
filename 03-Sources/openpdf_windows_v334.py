"""Compatibilité V33.4 sans altération de l’espace global de V33.3."""
from openpdf_windows_v333 import OpenPDFStudio as Previous
class OpenPDFStudio(Previous):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.title("OpenPDF Studio V33.4 — Abdelhalim Talbi")
if __name__ == "__main__":
    OpenPDFStudio().mainloop()
