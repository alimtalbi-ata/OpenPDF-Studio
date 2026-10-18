"""OpenPDF Studio V26.6 — workspace Windows. Auteur : Abdelhalim Talbi."""
from openpdf_windows_v265 import OpenPDFStudio as StudioV265

class OpenPDFStudio(StudioV265):
    def __init__(self):
        super().__init__()
        self.title('OpenPDF Studio V26.6 — Abdelhalim Talbi')
        self.geometry('1320x840')
        self.minsize(960,620)
        self._install_shortcuts()

    def _install_shortcuts(self):
        self.bind_all('<Control-o>',lambda event:self.add_files())
        self.bind_all('<Control-s>',lambda event:self.editor.save() if self.editor.source else None)
        self.bind_all('<Control-Return>',lambda event:self.run())

if __name__=='__main__':
    OpenPDFStudio().mainloop()
