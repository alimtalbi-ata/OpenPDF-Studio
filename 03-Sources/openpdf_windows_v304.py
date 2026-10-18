"""OpenPDF Studio V30.4 — Abdelhalim Talbi."""
from openpdf_windows_v293 import OpenPDFStudio as ApplicationCore
from openpdf_workspace_v304 import connect

class OpenPDFStudio(ApplicationCore):
    """Ensure both direct class construction and create_app use all bridges."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title('OpenPDF Studio V30.4 — Abdelhalim Talbi')
        connect(self)

def create_app():
    return OpenPDFStudio()

if __name__ == '__main__':
    create_app().mainloop()
