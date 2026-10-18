"""OpenPDF Studio V31.0 — Abdelhalim Talbi."""
from openpdf_windows_v309 import OpenPDFStudio as Previous
from openpdf_ui_bridge_v310 import connect, dispatch_selected

class OpenPDFStudio(Previous):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        connect(self)
        self.title('OpenPDF Studio V31.0 — Abdelhalim Talbi')

    def run(self):
        routed = dispatch_selected(self)
        if routed is None:
            return super().run()
        return routed

def create_app():
    return OpenPDFStudio()

if __name__ == '__main__':
    create_app().mainloop()
