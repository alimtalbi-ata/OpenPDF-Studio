"""OpenPDF Studio V29.5 — point d’entrée unifié. Auteur : Abdelhalim Talbi."""
from openpdf_windows_v293 import OpenPDFStudio as ApplicationCore

def create_app():
    app = ApplicationCore()
    app.title("OpenPDF Studio V29.5 — Abdelhalim Talbi")
    return app

OpenPDFStudio = ApplicationCore  # compatibilité imports historiques

if __name__ == "__main__":
    create_app().mainloop()
