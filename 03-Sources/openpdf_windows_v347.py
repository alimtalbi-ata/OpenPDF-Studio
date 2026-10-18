"""V34.7: OCR service API; legacy GUI remains until UI migration is qualified."""
from openpdf_windows_v346 import OpenPDFStudio as Previous
from openpdf_ocr_service_v347 import searchable_pdf
class OpenPDFStudio(Previous):
    ocr_searchable_pdf=staticmethod(searchable_pdf)
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.title('OpenPDF Studio V34.7 — Abdelhalim Talbi')
if __name__=='__main__':OpenPDFStudio().mainloop()
