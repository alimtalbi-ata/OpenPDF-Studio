"""OpenPDF Studio V32.9 — Abdelhalim Talbi."""
from openpdf_windows_v328 import OpenPDFStudio as Previous
class OpenPDFStudio(Previous):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs)
  self.title('OpenPDF Studio V32.9 — Abdelhalim Talbi')
if __name__=='__main__':OpenPDFStudio().mainloop()
