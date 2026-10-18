"""OpenPDF Studio V29.6 — point d’entrée stable. Auteur : Abdelhalim Talbi."""
from openpdf_windows_v293 import OpenPDFStudio as ApplicationCore
from openpdf_commands_v296 import PDFCommands

def create_app():
    app = ApplicationCore()
    app.title("OpenPDF Studio V29.6 — Abdelhalim Talbi")
    app.pdf_commands = PDFCommands()
    return app

OpenPDFStudio = ApplicationCore
if __name__ == "__main__":
    create_app().mainloop()
