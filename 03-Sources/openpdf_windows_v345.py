"""V34.5: page services available to UI, legacy controls retained during migration."""
from openpdf_windows_v344 import OpenPDFStudio as Previous
from openpdf_page_service_v345 import merge,extract,reorder,split
class OpenPDFStudio(Previous):
    page_services={'merge':staticmethod(merge),'extract':staticmethod(extract),'reorder':staticmethod(reorder),'split':staticmethod(split)}
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.title('OpenPDF Studio V34.5 — Abdelhalim Talbi')
if __name__=='__main__':OpenPDFStudio().mainloop()
