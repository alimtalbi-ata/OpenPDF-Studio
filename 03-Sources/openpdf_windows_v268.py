"""OpenPDF Studio V26.8 Windows entrypoint. Author: Abdelhalim Talbi."""
from openpdf_windows_v267 import OpenPDFStudio

if __name__ == "__main__":
    app = OpenPDFStudio()
    app.title("OpenPDF Studio V26.8 — Abdelhalim Talbi")
    app.mainloop()
