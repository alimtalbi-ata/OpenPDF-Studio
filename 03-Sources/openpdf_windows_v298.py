"""OpenPDF Studio V29.8 — Abdelhalim Talbi."""
from openpdf_windows_v293 import OpenPDFStudio as ApplicationCore
from openpdf_ui_bridge_v298 import connect

def create_app():
    app = ApplicationCore()
    app.title('OpenPDF Studio V29.8 — Abdelhalim Talbi')
    return connect(app)

OpenPDFStudio = ApplicationCore
if __name__ == '__main__':
    create_app().mainloop()
