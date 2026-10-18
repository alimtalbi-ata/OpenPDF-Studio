"""V34.2: explicit operation registry integrated at the UI boundary.
Legacy UI remains until integration and native Windows testing succeed.
"""
from openpdf_windows_v341 import OpenPDFStudio as Previous
from openpdf_operations_v342 import OperationController, OperationRegistry

class OpenPDFStudio(Previous):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self._v342_registry=OperationRegistry()
        self._v342_controller=OperationController(self._v342_registry)
        self.title("OpenPDF Studio V34.2 — Abdelhalim Talbi")

if __name__ == "__main__":
    OpenPDFStudio().mainloop()
