"""OpenPDF Studio V28.1: audited Windows build entrypoint.
Author: Abdelhalim Talbi.
"""
from openpdf_windows_v280 import OpenPDFStudio as PreviousStudio

class OpenPDFStudio(PreviousStudio):
    def __init__(self):
        super().__init__()
        self.title('OpenPDF Studio V28.1 — Abdelhalim Talbi')

if __name__ == '__main__':
    OpenPDFStudio().mainloop()
